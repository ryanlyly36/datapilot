from uuid import uuid4

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.checks import (
    data_freshness,
    formula_sanity,
    numerator_denominator,
    segment_concentration,
    structural_anomaly,
    supporting_metrics,
)
from app.engines import driver_analysis, verdict_engine
from app.models.schemas import InvestigationRequest, InvestigationResponse
from app.registry.metric_registry import get_metric
from app.services.narrative_service import generate_narrative
from app.services.query_service import compute_topline, get_period_data, load_data

app = FastAPI(
    title="DataPilot API",
    description="AI-backed KPI investigation platform",
    version="0.1.0"
)

# Allow frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

df = load_data()


def _validate_investigation_windows(request: InvestigationRequest) -> None:
    baseline_start = pd.Timestamp(request.baseline_period_start)
    baseline_end = pd.Timestamp(request.baseline_period_end)
    comparison_start = pd.Timestamp(request.comparison_period_start)
    comparison_end = pd.Timestamp(request.comparison_period_end)

    if baseline_start > baseline_end:
        raise HTTPException(
            status_code=400,
            detail="Invalid baseline window: baseline_period_start must be on or before baseline_period_end.",
        )

    if comparison_start > comparison_end:
        raise HTTPException(
            status_code=400,
            detail="Invalid comparison window: comparison_period_start must be on or before comparison_period_end.",
        )

    baseline_df = get_period_data(df, request.baseline_period_start, request.baseline_period_end)
    if baseline_df.empty:
        raise HTTPException(
            status_code=400,
            detail="Invalid baseline window: no data found for the requested baseline period.",
        )

    comparison_df = get_period_data(df, request.comparison_period_start, request.comparison_period_end)
    if comparison_df.empty:
        raise HTTPException(
            status_code=400,
            detail="Invalid comparison window: no data found for the requested comparison period.",
        )

@app.get("/")
def root():
    return {"status": "ok", "message": "DataPilot API is running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/investigate", response_model=InvestigationResponse)
def investigate(request: InvestigationRequest):
    try:
        metric = get_metric(request.metric_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    _validate_investigation_windows(request)

    topline = compute_topline(
        df,
        request.baseline_period_start,
        request.baseline_period_end,
        request.comparison_period_start,
        request.comparison_period_end,
        metric.numerator,
        metric.denominator,
    )

    checks = [
        data_freshness.run(
            df,
            metric,
            request.baseline_period_start,
            request.baseline_period_end,
            request.comparison_period_start,
            request.comparison_period_end,
            topline,
        ),
        formula_sanity.run(
            df,
            metric,
            request.baseline_period_start,
            request.baseline_period_end,
            request.comparison_period_start,
            request.comparison_period_end,
            topline,
        ),
        structural_anomaly.run(
            df,
            metric,
            request.baseline_period_start,
            request.baseline_period_end,
            request.comparison_period_start,
            request.comparison_period_end,
            topline,
        ),
        numerator_denominator.run(
            df,
            metric,
            request.baseline_period_start,
            request.baseline_period_end,
            request.comparison_period_start,
            request.comparison_period_end,
            topline,
        ),
        segment_concentration.run(
            df,
            metric,
            request.baseline_period_start,
            request.baseline_period_end,
            request.comparison_period_start,
            request.comparison_period_end,
            topline,
            request.dimensions,
        ),
        supporting_metrics.run(
            df,
            metric,
            request.baseline_period_start,
            request.baseline_period_end,
            request.comparison_period_start,
            request.comparison_period_end,
            topline,
        ),
    ]

    verdict = verdict_engine.run(checks)
    top_drivers = driver_analysis.run(
        df,
        metric,
        request.baseline_period_start,
        request.baseline_period_end,
        request.comparison_period_start,
        request.comparison_period_end,
        topline,
        request.dimensions,
    )
    narrative = generate_narrative(
        metric_name=request.metric_name,
        topline=topline,
        checks=checks,
        verdict=verdict,
        top_drivers=top_drivers,
    )

    return InvestigationResponse(
        investigation_id=str(uuid4()),
        metric_name=request.metric_name,
        comparison={
            "baseline_period_start": request.baseline_period_start,
            "baseline_period_end": request.baseline_period_end,
            "comparison_period_start": request.comparison_period_start,
            "comparison_period_end": request.comparison_period_end,
        },
        topline=topline,
        checks=checks,
        verdict=verdict,
        top_drivers=top_drivers,
        narrative=narrative,
    )

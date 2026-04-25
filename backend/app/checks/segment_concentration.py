from app.models.schemas import CheckResult, CheckStatus, CheckSeverity, CheckType
from app.registry.metric_registry import MetricDefinition
from app.services.query_service import compute_segment_breakdown
import pandas as pd

MIN_SEGMENT_DELTA = 0.001

def run(
    df: pd.DataFrame,
    metric: MetricDefinition,
    baseline_start: str,
    baseline_end: str,
    comparison_start: str,
    comparison_end: str,
    topline: dict,
    dimensions: list[str]
) -> CheckResult:
    evidence = []
    concentrated_segments = []

    total_delta = abs(topline["absolute_delta"])
    if total_delta < MIN_SEGMENT_DELTA:
        return CheckResult(
            check_name="segment_concentration",
            check_type=CheckType.business,
            status=CheckStatus.pass_,
            severity=CheckSeverity.low,
            summary="No meaningful delta to analyze for segment concentration.",
            details={},
            evidence=["Total delta is zero or near zero"]
        )

    for dimension in dimensions:
        breakdown = compute_segment_breakdown(
            df,
            baseline_start, baseline_end,
            comparison_start, comparison_end,
            metric.numerator, metric.denominator,
            dimension
        )

        for segment in breakdown:
            seg_delta = abs(segment["contribution_delta"])
            contribution = (seg_delta / total_delta * 100) if total_delta > 0 else 0
            if contribution >= 30:
                concentrated_segments.append({
                    "dimension": dimension,
                    "segment": segment["segment"],
                    "contribution_pct": round(contribution, 1),
                    "delta": segment["contribution_delta"]
                })
                evidence.append(
                    f"{dimension}={segment['segment']} contributed ~{contribution:.1f}% of total delta"
                )

    if concentrated_segments:
        top = concentrated_segments[0]
        return CheckResult(
            check_name="segment_concentration",
            check_type=CheckType.business,
            status=CheckStatus.warning,
            severity=CheckSeverity.medium,
            summary=f"High concentration detected: {top['dimension']}={top['segment']} explains ~{top['contribution_pct']}% of the delta.",
            details={"concentrated_segments": concentrated_segments},
            evidence=evidence
        )

    return CheckResult(
        check_name="segment_concentration",
        check_type=CheckType.business,
        status=CheckStatus.pass_,
        severity=CheckSeverity.low,
        summary="Delta is spread across multiple segments. No single segment dominates.",
        details={},
        evidence=evidence
    )

from app.models.schemas import TopDriver, DriverDirection
from app.registry.metric_registry import MetricDefinition
from app.services.query_service import compute_segment_breakdown
import pandas as pd

MIN_DRIVER_DELTA = 0.001

def run(
    df: pd.DataFrame,
    metric: MetricDefinition,
    baseline_start: str,
    baseline_end: str,
    comparison_start: str,
    comparison_end: str,
    topline: dict,
    dimensions: list[str]
) -> list[TopDriver]:
    total_delta = topline["absolute_delta"]
    drivers = []

    if abs(total_delta) < MIN_DRIVER_DELTA:
        return []

    for dimension in dimensions:
        breakdown = compute_segment_breakdown(
            df,
            baseline_start, baseline_end,
            comparison_start, comparison_end,
            metric.numerator, metric.denominator,
            dimension
        )

        for segment in breakdown:
            seg_delta = segment["contribution_delta"]

            contribution_pct = round(abs(seg_delta / total_delta) * 100, 1)

            if contribution_pct < 5:
                continue

            direction = DriverDirection.negative if seg_delta < 0 else DriverDirection.positive
            pct_delta = segment["pct_delta"]
            pct_delta_text = "new or previously absent segment"
            if pct_delta is not None:
                pct_delta_text = f"{pct_delta:+.1f}%"

            summary = (
                f"{dimension}={segment['segment']} conversion rate changed "
                f"{pct_delta_text} "
                f"({'drag' if direction == DriverDirection.negative else 'lift'} on overall metric)"
            )

            drivers.append(TopDriver(
                dimension=dimension,
                segment=str(segment["segment"]),
                contribution_pct=contribution_pct,
                direction=direction,
                summary=summary
            ))

    # Sort by contribution, biggest first
    drivers.sort(key=lambda x: x.contribution_pct, reverse=True)

    # Return top 5
    return drivers[:5]

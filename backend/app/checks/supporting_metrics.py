from app.models.schemas import CheckResult, CheckSeverity, CheckStatus, CheckType
from app.registry.metric_registry import MetricDefinition
from app.services.query_service import get_period_data
import pandas as pd

MIN_SUPPORTING_DELTA_PCT = 5
MIN_TOPLINE_DELTA = 0.001

SUPPORTING_METRICS = [
    "add_to_cart",
    "checkout_start",
    "revenue",
]


def run(
    df: pd.DataFrame,
    metric: MetricDefinition,
    baseline_start: str,
    baseline_end: str,
    comparison_start: str,
    comparison_end: str,
    topline: dict
) -> CheckResult:
    evidence = []
    aligned_metrics = []
    contradictory_metrics = []
    neutral_metrics = []

    baseline_df = get_period_data(df, baseline_start, baseline_end)
    comparison_df = get_period_data(df, comparison_start, comparison_end)

    absolute_delta = topline["absolute_delta"]
    if abs(absolute_delta) < MIN_TOPLINE_DELTA:
        return CheckResult(
            check_name="supporting_metrics_consistency",
            check_type=CheckType.business,
            status=CheckStatus.pass_,
            severity=CheckSeverity.low,
            summary="No meaningful topline movement to validate with supporting metrics.",
            details={},
            evidence=["Topline delta is too small for a meaningful supporting-metric consistency check."],
        )

    expected_direction = "up" if absolute_delta > 0 else "down"

    for col in SUPPORTING_METRICS:
        if col not in df.columns:
            continue

        base_val = baseline_df[col].sum()
        comp_val = comparison_df[col].sum()

        if base_val == 0:
            evidence.append(f"{col}: skipped because baseline value is zero")
            continue

        delta_pct = (comp_val - base_val) / base_val * 100
        magnitude = abs(delta_pct)

        if magnitude < MIN_SUPPORTING_DELTA_PCT:
            neutral_metrics.append({
                "metric": col,
                "delta_pct": round(delta_pct, 2),
            })
            evidence.append(
                f"{col}: {delta_pct:.2f}% change (below {MIN_SUPPORTING_DELTA_PCT}% materiality threshold)"
            )
            continue

        actual_direction = "up" if delta_pct > 0 else "down"
        evidence.append(
            f"{col}: {delta_pct:.2f}% change (expected to move {expected_direction})"
        )

        metric_result = {
            "metric": col,
            "delta_pct": round(delta_pct, 2),
            "direction": actual_direction,
        }

        if actual_direction == expected_direction:
            aligned_metrics.append(metric_result)
        else:
            contradictory_metrics.append(metric_result)

    details = {
        "expected_direction": expected_direction,
        "aligned_metrics": aligned_metrics,
        "contradictory_metrics": contradictory_metrics,
        "neutral_metrics": neutral_metrics,
    }

    if len(contradictory_metrics) >= 2:
        return CheckResult(
            check_name="supporting_metrics_consistency",
            check_type=CheckType.business,
            status=CheckStatus.fail,
            severity=CheckSeverity.high,
            summary="Supporting metrics materially contradict the KPI movement.",
            details=details,
            evidence=evidence,
        )

    if contradictory_metrics:
        return CheckResult(
            check_name="supporting_metrics_consistency",
            check_type=CheckType.business,
            status=CheckStatus.warning,
            severity=CheckSeverity.medium,
            summary="Supporting metrics are mixed: at least one material supporting metric moved against the KPI.",
            details=details,
            evidence=evidence,
        )

    if aligned_metrics:
        return CheckResult(
            check_name="supporting_metrics_consistency",
            check_type=CheckType.business,
            status=CheckStatus.pass_,
            severity=CheckSeverity.low,
            summary="Supporting metrics materially align with the KPI movement.",
            details=details,
            evidence=evidence,
        )

    return CheckResult(
        check_name="supporting_metrics_consistency",
        check_type=CheckType.business,
        status=CheckStatus.warning,
        severity=CheckSeverity.low,
        summary="Supporting metrics are mostly flat, so they do not provide strong confirmation of the KPI movement.",
        details=details,
        evidence=evidence,
    )

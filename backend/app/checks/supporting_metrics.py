from app.models.schemas import CheckResult, CheckStatus, CheckSeverity, CheckType
from app.registry.metric_registry import MetricDefinition
from app.services.query_service import get_period_data
import pandas as pd

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
    inconsistencies = []

    baseline_df = get_period_data(df, baseline_start, baseline_end)
    comparison_df = get_period_data(df, comparison_start, comparison_end)

    rate_direction = "down" if topline["absolute_delta"] < 0 else "up"

    supporting = {
        "add_to_cart": "down",   # expected direction if conversion drops
        "checkout_start": "down",
        "revenue": "down",
    }

    for col, expected_direction in supporting.items():
        if col not in df.columns:
            continue

        base_val = baseline_df[col].sum()
        comp_val = comparison_df[col].sum()

        if base_val == 0:
            continue

        delta_pct = (comp_val - base_val) / base_val * 100
        actual_direction = "down" if delta_pct < 0 else "up"

        evidence.append(f"{col}: {delta_pct:.2f}% change (expected: {expected_direction})")

        if rate_direction == "down" and actual_direction != expected_direction and abs(delta_pct) > 5:
            inconsistencies.append(f"{col} moved {actual_direction} ({delta_pct:.2f}%) but conversion moved {rate_direction}")

    if inconsistencies:
        return CheckResult(
            check_name="supporting_metrics_consistency",
            check_type=CheckType.business,
            status=CheckStatus.warning,
            severity=CheckSeverity.medium,
            summary=f"Some supporting metrics don't align with the conversion rate movement.",
            details={"inconsistencies": inconsistencies},
            evidence=evidence
        )

    return CheckResult(
        check_name="supporting_metrics_consistency",
        check_type=CheckType.business,
        status=CheckStatus.pass_,
        severity=CheckSeverity.low,
        summary="Supporting metrics move consistently with the conversion rate change.",
        details={},
        evidence=evidence
    )
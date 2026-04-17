from app.models.schemas import CheckResult, CheckStatus, CheckSeverity, CheckType
from app.registry.metric_registry import MetricDefinition
from app.services.query_service import get_period_data
import pandas as pd
from datetime import datetime, timedelta

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
    issues = []

    for label, start, end in [
        ("baseline", baseline_start, baseline_end),
        ("comparison", comparison_start, comparison_end)
    ]:
        period_df = get_period_data(df, start, end)
        expected_days = (pd.Timestamp(end) - pd.Timestamp(start)).days + 1
        actual_days = period_df["date"].nunique()

        evidence.append(f"{label} period: {actual_days}/{expected_days} days present")

        if actual_days < expected_days:
            issues.append(f"{label} period is missing {expected_days - actual_days} day(s) of data")

        # Check for suspicious row count drops
        daily_counts = period_df.groupby("date").size()
        if len(daily_counts) > 1:
            avg = daily_counts.mean()
            min_count = daily_counts.min()
            if min_count < avg * 0.5:
                issues.append(f"{label} period has a day with unusually low row count: {int(min_count)} vs avg {avg:.0f}")
                evidence.append(f"{label} min daily rows: {int(min_count)}, avg: {avg:.0f}")

    if issues:
        return CheckResult(
            check_name="data_freshness_completeness",
            check_type=CheckType.trust,
            status=CheckStatus.warning,
            severity=CheckSeverity.high,
            summary=f"Data completeness issues detected: {'; '.join(issues)}",
            details={"issues": issues},
            evidence=evidence
        )

    return CheckResult(
        check_name="data_freshness_completeness",
        check_type=CheckType.trust,
        status=CheckStatus.pass_,
        severity=CheckSeverity.low,
        summary="All required dates are present for both comparison periods.",
        details={},
        evidence=evidence
    )
from app.models.schemas import CheckResult, CheckStatus, CheckSeverity, CheckType
from app.registry.metric_registry import MetricDefinition
from app.services.query_service import get_period_data
import pandas as pd

CATEGORICAL_DIMS = ["device_type", "traffic_source", "region", "product_category"]

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

    baseline_df = get_period_data(df, baseline_start, baseline_end)
    comparison_df = get_period_data(df, comparison_start, comparison_end)

    # Check for null spikes
    for col in [metric.numerator, metric.denominator]:
        base_nulls = baseline_df[col].isnull().sum()
        comp_nulls = comparison_df[col].isnull().sum()
        if comp_nulls > base_nulls * 2 and comp_nulls > 10:
            issues.append(f"Null spike in {col}: {base_nulls} -> {comp_nulls}")
        evidence.append(f"Nulls in {col}: baseline={base_nulls}, comparison={comp_nulls}")

    # Check for disappearing or appearing categories
    for dim in CATEGORICAL_DIMS:
        if dim not in df.columns:
            continue
        base_vals = set(baseline_df[dim].dropna().unique())
        comp_vals = set(comparison_df[dim].dropna().unique())

        disappeared = base_vals - comp_vals
        appeared = comp_vals - base_vals

        if disappeared:
            issues.append(f"{dim} values disappeared in comparison: {disappeared}")
            evidence.append(f"{dim} lost categories: {disappeared}")
        if appeared:
            issues.append(f"{dim} new values appeared in comparison: {appeared}")
            evidence.append(f"{dim} gained categories: {appeared}")

    # Check for extreme outliers in numerator
    base_max = baseline_df[metric.numerator].max()
    comp_max = comparison_df[metric.numerator].max()
    if comp_max > base_max * 5:
        issues.append(f"Extreme outlier in {metric.numerator}: max jumped from {base_max} to {comp_max}")

    if issues:
        return CheckResult(
            check_name="structural_anomaly",
            check_type=CheckType.trust,
            status=CheckStatus.warning,
            severity=CheckSeverity.high,
            summary=f"Structural anomalies detected: {'; '.join(issues[:2])}",
            details={"issues": issues},
            evidence=evidence
        )

    return CheckResult(
        check_name="structural_anomaly",
        check_type=CheckType.trust,
        status=CheckStatus.pass_,
        severity=CheckSeverity.low,
        summary="No structural anomalies detected. Schema and categories are consistent across periods.",
        details={},
        evidence=evidence
    )
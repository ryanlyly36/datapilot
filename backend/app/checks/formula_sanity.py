from app.models.schemas import CheckResult, CheckStatus, CheckSeverity, CheckType
from app.registry.metric_registry import MetricDefinition
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
    issues = []

    # Check numerator column exists
    if metric.numerator not in df.columns:
        issues.append(f"Numerator column '{metric.numerator}' not found in data")
    else:
        evidence.append(f"Numerator column '{metric.numerator}' exists")

    # Check denominator column exists
    if metric.denominator not in df.columns:
        issues.append(f"Denominator column '{metric.denominator}' not found in data")
    else:
        evidence.append(f"Denominator column '{metric.denominator}' exists")

    # Check denominator is not near zero
    baseline_den = topline.get("baseline_denominator", 0)
    comparison_den = topline.get("comparison_denominator", 0)

    if baseline_den < 100:
        issues.append(f"Baseline denominator is very low: {baseline_den}")
    else:
        evidence.append(f"Baseline denominator is healthy: {baseline_den}")

    if comparison_den < 100:
        issues.append(f"Comparison denominator is very low: {comparison_den}")
    else:
        evidence.append(f"Comparison denominator is healthy: {comparison_den}")

    if issues:
        return CheckResult(
            check_name="formula_sanity",
            check_type=CheckType.trust,
            status=CheckStatus.fail,
            severity=CheckSeverity.high,
            summary=f"Formula sanity issues found: {'; '.join(issues)}",
            details={"issues": issues},
            evidence=evidence
        )

    return CheckResult(
        check_name="formula_sanity",
        check_type=CheckType.trust,
        status=CheckStatus.pass_,
        severity=CheckSeverity.low,
        summary="Metric formula is valid. Numerator and denominator exist and are healthy.",
        details={},
        evidence=evidence
    )
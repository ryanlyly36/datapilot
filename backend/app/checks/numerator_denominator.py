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

    baseline_num = topline["baseline_numerator"]
    baseline_den = topline["baseline_denominator"]
    comparison_num = topline["comparison_numerator"]
    comparison_den = topline["comparison_denominator"]

    num_delta_pct = ((comparison_num - baseline_num) / baseline_num * 100) if baseline_num > 0 else 0
    den_delta_pct = ((comparison_den - baseline_den) / baseline_den * 100) if baseline_den > 0 else 0
    rate_delta_pct = topline["percent_delta"]

    evidence.append(f"{metric.numerator} changed {num_delta_pct:.2f}% ({baseline_num} -> {comparison_num})")
    evidence.append(f"{metric.denominator} changed {den_delta_pct:.2f}% ({baseline_den} -> {comparison_den})")
    evidence.append(f"Conversion rate changed {rate_delta_pct:.2f}%")

    # Suspicious: numerator collapsed while denominator stable
    if num_delta_pct < -20 and abs(den_delta_pct) < 5:
        return CheckResult(
            check_name="numerator_denominator_direction",
            check_type=CheckType.business,
            status=CheckStatus.warning,
            severity=CheckSeverity.high,
            summary=f"{metric.numerator} dropped sharply while {metric.denominator} stayed stable — possible tracking issue.",
            details={
                "numerator_delta_pct": round(num_delta_pct, 2),
                "denominator_delta_pct": round(den_delta_pct, 2)
            },
            evidence=evidence
        )

    # Denominator spiked while numerator flat — explains conversion drop
    if den_delta_pct > 15 and abs(num_delta_pct) < 5:
        return CheckResult(
            check_name="numerator_denominator_direction",
            check_type=CheckType.business,
            status=CheckStatus.warning,
            severity=CheckSeverity.medium,
            summary=f"{metric.denominator} increased significantly while {metric.numerator} stayed flat — dilution effect likely explains conversion drop.",
            details={
                "numerator_delta_pct": round(num_delta_pct, 2),
                "denominator_delta_pct": round(den_delta_pct, 2)
            },
            evidence=evidence
        )

    return CheckResult(
        check_name="numerator_denominator_direction",
        check_type=CheckType.business,
        status=CheckStatus.pass_,
        severity=CheckSeverity.low,
        summary=f"Numerator and denominator movement is consistent with the reported rate change.",
        details={
            "numerator_delta_pct": round(num_delta_pct, 2),
            "denominator_delta_pct": round(den_delta_pct, 2)
        },
        evidence=evidence
    )
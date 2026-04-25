from app.models.schemas import CheckResult, CheckStatus, CheckType, Verdict, VerdictLabel, VerdictConfidence

def run(checks: list[CheckResult]) -> Verdict:
    trust_checks = [c for c in checks if c.check_type == "trust"]
    business_checks = [c for c in checks if c.check_type == "business"]

    trust_failures = [c for c in trust_checks if c.status in ("warning", "fail")]
    business_warnings = [c for c in business_checks if c.status in ("warning", "fail")]

    trust_fail_count = len(trust_failures)
    business_warn_count = len(business_warnings)

    # Decision logic — backend owned, no LLM involved
    if trust_fail_count >= 2:
        label = VerdictLabel.possible_data_issue
        confidence = VerdictConfidence.high
        summary = (
            "Multiple trust checks failed. The metric change may be driven by "
            "data quality, freshness, or structural issues rather than real business behavior."
        )

    elif trust_fail_count == 1 and business_warn_count >= 1:
        label = VerdictLabel.mixed_or_unclear
        confidence = VerdictConfidence.low
        summary = (
            "One trust check failed and business signals are mixed. "
            "It is unclear whether this is a real business shift or a data issue. "
            "Further investigation is recommended."
        )

    elif trust_fail_count == 1:
        label = VerdictLabel.mixed_or_unclear
        confidence = VerdictConfidence.medium
        summary = (
            "One trust check flagged a potential issue. "
            "Business signals look reasonable but data quality should be verified."
        )

    elif business_warn_count >= 1:
        label = VerdictLabel.likely_business_shift
        confidence = VerdictConfidence.medium
        summary = (
            "Trust checks passed. Business signals show segment concentration "
            "or supporting metric movement consistent with a real business shift."
        )

    else:
        label = VerdictLabel.likely_business_shift
        confidence = VerdictConfidence.high
        summary = (
            "All trust checks passed and business signals are consistent. "
            "The metric change appears to reflect real business behavior."
        )

    return Verdict(
        label=label,
        confidence=confidence,
        summary=summary
    )
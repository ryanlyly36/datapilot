import logging
import os

import anthropic
from dotenv import load_dotenv

from app.models.schemas import CheckResult, TopDriver, Verdict

load_dotenv()

logger = logging.getLogger(__name__)


def _create_client() -> anthropic.Anthropic | None:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    return anthropic.Anthropic(api_key=api_key)


def _build_fallback_narrative(
    metric_name: str,
    topline: dict,
    verdict_label: str,
    verdict: Verdict,
    top_drivers: list[TopDriver],
) -> str:
    absolute_delta = topline["absolute_delta"]
    percent_delta = topline["percent_delta"]

    if abs(absolute_delta) < 0.001:
        movement_summary = (
            f"{metric_name} was broadly flat week over week, with little net change in the topline."
        )
    else:
        direction = "increased" if absolute_delta > 0 else "decreased"
        movement_summary = (
            f"{metric_name} {direction} week over week by {abs(percent_delta):.2f}%."
        )

    if top_drivers:
        top_driver = top_drivers[0]
        driver_summary = (
            f"The strongest segment-level signal was {top_driver.dimension}={top_driver.segment}, "
            f"which acted as a {top_driver.direction.value} on the metric."
        )
    else:
        driver_summary = "No single segment cleared the current driver threshold."

    return (
        "Rule-based summary: "
        f"{movement_summary} "
        f"The current verdict is {verdict_label}. "
        f"{verdict.summary} "
        f"{driver_summary} "
        "Next step: review the trust checks and the top segment-level drivers together."
    )


def generate_narrative(
    metric_name: str,
    topline: dict,
    checks: list[CheckResult],
    verdict: Verdict,
    top_drivers: list[TopDriver]
) -> str:
    verdict_label = getattr(verdict.label, "value", verdict.label)
    verdict_confidence = getattr(verdict.confidence, "value", verdict.confidence)

    check_summaries = "\n".join(
        f"- {c.check_name} ({c.status}): {c.summary}"
        for c in checks
    )

    driver_summaries = "\n".join(
        f"- {d.dimension}={d.segment}: {d.contribution_pct}% contribution, {d.direction} ({d.summary})"
        for d in top_drivers
    )

    prompt = f"""You are a data analyst writing a brief investigation summary for a product team.

Here are the already-computed findings. Do not make up any numbers or conclusions - only summarize what is provided.

METRIC: {metric_name}
TOPLINE:
- Baseline value: {topline['baseline_value']}
- Comparison value: {topline['comparison_value']}
- Absolute delta: {topline['absolute_delta']}
- Percent delta: {topline['percent_delta']}%

VERDICT: {verdict_label} (confidence: {verdict_confidence})
{verdict.summary}

EVIDENCE CHECKS:
{check_summaries}

TOP DRIVERS:
{driver_summaries}

Write a 3-5 sentence plain English explanation of what likely happened.
Be direct and specific. Do not use bullet points. Do not repeat the numbers verbatim - synthesize them into a readable narrative.
End with one sentence about recommended next steps."""

    client = _create_client()
    if client is None:
        logger.info("ANTHROPIC_API_KEY not set; using rule-based narrative fallback.")
        return _build_fallback_narrative(
            metric_name=metric_name,
            topline=topline,
            verdict_label=verdict_label,
            verdict=verdict,
            top_drivers=top_drivers,
        )

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text
    except Exception as exc:
        logger.warning("Anthropic narrative generation failed; using fallback narrative: %s", exc)
        return _build_fallback_narrative(
            metric_name=metric_name,
            topline=topline,
            verdict_label=verdict_label,
            verdict=verdict,
            top_drivers=top_drivers,
        )

from typing import Optional

# --- Metric Definition ---

class MetricDefinition:
    def __init__(
        self,
        name: str,
        numerator: str,
        denominator: str,
        description: str,
        supporting_metrics: Optional[list[str]] = None
    ):
        self.name = name
        self.numerator = numerator
        self.denominator = denominator
        self.description = description
        self.supporting_metrics = supporting_metrics or []


# --- Registry ---

METRIC_REGISTRY: dict[str, MetricDefinition] = {
    "conversion_rate": MetricDefinition(
        name="conversion_rate",
        numerator="orders",
        denominator="sessions",
        description="Percentage of sessions that result in an order",
        supporting_metrics=[
            "add_to_cart",
            "checkout_start",
            "bounce_rate",
            "revenue"
        ]
    )
}


def get_metric(metric_name: str) -> Optional[MetricDefinition]:
    return METRIC_REGISTRY.get(metric_name)


def list_metrics() -> list[str]:
    return list(METRIC_REGISTRY.keys())
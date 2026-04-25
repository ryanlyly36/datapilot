from dataclasses import dataclass


@dataclass
class MetricDefinition:
    metric_name: str
    numerator: str
    denominator: str


METRIC_REGISTRY: dict[str, MetricDefinition] = {
    "conversion_rate": MetricDefinition(
        metric_name="conversion_rate",
        numerator="orders",
        denominator="sessions",
    )
}


def get_metric(metric_name: str) -> MetricDefinition:
    if metric_name not in METRIC_REGISTRY:
        raise ValueError(f"Unknown metric: {metric_name}")
    return METRIC_REGISTRY[metric_name]
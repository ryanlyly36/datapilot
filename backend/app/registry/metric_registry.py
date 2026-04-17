from dataclasses import dataclass


@dataclass
class MetricDefinition:
    metric_name: str
    numerator_column: str
    denominator_column: str


METRIC_REGISTRY: dict[str, MetricDefinition] = {
    "conversion_rate": MetricDefinition(
        metric_name="conversion_rate",
        numerator_column="orders",
        denominator_column="sessions",
    )
}
from pydantic import BaseModel
from typing import Optional
from enum import Enum


# --- Enums ---

class CheckStatus(str, Enum):
    pass_ = "pass"
    warning = "warning"
    fail = "fail"

class CheckSeverity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class CheckType(str, Enum):
    trust = "trust"
    business = "business"

class VerdictLabel(str, Enum):
    likely_business_shift = "likely_business_shift"
    possible_data_issue = "possible_data_issue"
    mixed_or_unclear = "mixed_or_unclear"

class VerdictConfidence(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class DriverDirection(str, Enum):
    positive = "positive"
    negative = "negative"


# --- Check Result ---

class CheckResult(BaseModel):
    check_name: str
    check_type: CheckType
    status: CheckStatus
    severity: CheckSeverity
    summary: str
    details: dict = {}
    evidence: list = []


# --- Verdict ---

class Verdict(BaseModel):
    label: VerdictLabel
    confidence: VerdictConfidence
    summary: str


# --- Top Driver ---

class TopDriver(BaseModel):
    dimension: str
    segment: str
    contribution_pct: float
    direction: DriverDirection
    summary: str


# --- Topline Comparison ---

class ToplineComparison(BaseModel):
    baseline_value: float
    comparison_value: float
    absolute_delta: float
    percent_delta: float


# --- Investigation Request ---

class InvestigationRequest(BaseModel):
    metric_name: str
    baseline_period_start: str
    baseline_period_end: str
    comparison_period_start: str
    comparison_period_end: str
    dimensions: Optional[list[str]] = ["device_type", "traffic_source", "region", "product_category"]


# --- Investigation Response ---

class InvestigationResponse(BaseModel):
    investigation_id: str
    metric_name: str
    comparison: dict
    topline: ToplineComparison
    checks: list[CheckResult]
    verdict: Verdict
    top_drivers: list[TopDriver]
    narrative: str
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class CaseStatus(StrEnum):
    RECEIVED = "received"
    ANALYZED = "analyzed"
    REVIEW_REQUIRED = "review_required"
    APPROVED = "approved"
    EXECUTION_QUEUED = "execution_queued"
    EXECUTING = "executing"
    EXECUTED = "executed"
    FAILED = "failed"


class RiskLevel(StrEnum):
    LOW = "low"
    HIGH = "high"


class CaseCreate(BaseModel):
    document_text: str = Field(min_length=1, max_length=20_000)
    source: str = Field(default="api", min_length=1, max_length=50)


class ExtractedCase(BaseModel):
    supplier: str | None = None
    invoice_number: str | None = None
    invoice_date: str | None = None
    currency: str | None = None
    total_amount: float | None = Field(default=None, ge=0)
    purchase_order: str | None = None
    confidence: float = Field(ge=0, le=1)
    risk_level: RiskLevel
    risk_flags: list[str] = Field(default_factory=list)
    recommended_action: str


class ToolCall(BaseModel):
    tool_name: str
    arguments: dict[str, Any]


class AnalysisResult(BaseModel):
    extraction: ExtractedCase
    proposed_tool: ToolCall | None = None
    requires_human_review: bool
    policy_reasons: list[str] = Field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0


class CaseView(BaseModel):
    case_id: str
    status: CaseStatus
    source: str
    analysis: AnalysisResult | None = None
    execution_result: dict[str, Any] | None = None


class AuditEvent(BaseModel):
    event: str
    detail: str
    created_at: str


class Metrics(BaseModel):
    total_cases: int
    by_status: dict[str, int]
    total_input_tokens: int
    total_output_tokens: int
    estimated_cost_usd: float
    execution_queue_depth: int = 0
    review_required_count: int = 0

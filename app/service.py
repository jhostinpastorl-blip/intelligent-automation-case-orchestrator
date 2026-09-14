from uuid import uuid4

from app.dispatch import get_dispatch_queue
from app.models import AnalysisResult, CaseCreate, CaseStatus, CaseView
from app.policy import evaluate_policy
from app.provider import get_provider
from app.store import CaseRecord, store


class CaseService:
    def create(self, request: CaseCreate) -> CaseView:
        record = CaseRecord(
            case_id=str(uuid4()),
            document_text=request.document_text,
            source=request.source,
            status=CaseStatus.RECEIVED,
        )
        store.put(record)
        store.event(record, "case_received", "Case accepted for controlled analysis")
        return self._view(record)

    def get(self, case_id: str) -> CaseView | None:
        record = store.get(case_id)
        return self._view(record) if record else None

    def analyze(self, case_id: str) -> CaseView:
        record = self._require(case_id)
        response = get_provider().analyze(record.document_text)
        review, reasons, tool = evaluate_policy(response.extraction)
        record.analysis = AnalysisResult(
            extraction=response.extraction,
            proposed_tool=tool,
            requires_human_review=review,
            policy_reasons=reasons,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            estimated_cost_usd=response.estimated_cost_usd,
        )
        record.status = CaseStatus.REVIEW_REQUIRED if review else CaseStatus.ANALYZED
        store.save(record)
        store.record_usage(
            record.case_id,
            response.input_tokens,
            response.output_tokens,
            response.estimated_cost_usd,
        )
        store.event(record, "analysis_completed", f"review={review}; reasons={reasons}")
        return self._view(record)

    def approve(self, case_id: str) -> CaseView:
        record = self._require(case_id)
        if record.status != CaseStatus.REVIEW_REQUIRED:
            raise ValueError("Only review-required cases can be approved")
        record.status = CaseStatus.APPROVED
        store.save(record)
        store.event(record, "human_approved", "Human reviewer approved the proposed controlled action")
        return self._view(record)

    def execute(self, case_id: str) -> CaseView:
        record = self._require(case_id)
        if record.analysis is None or record.analysis.proposed_tool is None:
            raise ValueError("Case has no analyzed tool call")
        if record.analysis.requires_human_review and record.status != CaseStatus.APPROVED:
            raise ValueError("Human approval is required before execution")
        if not record.analysis.requires_human_review and record.status != CaseStatus.ANALYZED:
            raise ValueError("Case is not ready for execution")
        record.status = CaseStatus.EXECUTION_QUEUED
        store.save(record)
        store.event(record, "execution_queued", "Approved intent queued for controlled execution")
        get_dispatch_queue().publish(record.case_id)
        return self._view(record)

    def audit(self, case_id: str):
        self._require(case_id)
        return store.audit(case_id)

    @staticmethod
    def _require(case_id: str) -> CaseRecord:
        record = store.get(case_id)
        if record is None:
            raise KeyError(case_id)
        return record

    @staticmethod
    def _view(record: CaseRecord) -> CaseView:
        return CaseView(
            case_id=record.case_id,
            status=record.status,
            source=record.source,
            analysis=record.analysis,
            execution_result=record.execution_result,
        )

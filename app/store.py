from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, func, insert, select, update

from app.database import audit_events, cases, get_engine, metrics_ledger
from app.models import AnalysisResult, AuditEvent, CaseStatus, Metrics


def now() -> str:
    return datetime.now(UTC).isoformat()


class CaseRecord:
    def __init__(
        self,
        case_id: str,
        document_text: str,
        source: str,
        status: CaseStatus,
        analysis: AnalysisResult | None = None,
        execution_result: dict[str, Any] | None = None,
    ) -> None:
        self.case_id = case_id
        self.document_text = document_text
        self.source = source
        self.status = status
        self.analysis = analysis
        self.execution_result = execution_result


class SqlCaseStore:
    def put(self, record: CaseRecord) -> None:
        with get_engine().begin() as conn:
            conn.execute(insert(cases).values(
                case_id=record.case_id,
                document_text=record.document_text,
                source=record.source,
                status=record.status.value,
            ))

    def save(self, record: CaseRecord) -> None:
        with get_engine().begin() as conn:
            conn.execute(
                update(cases)
                .where(cases.c.case_id == record.case_id)
                .values(
                    status=record.status.value,
                    analysis_json=record.analysis.model_dump(mode="json") if record.analysis else None,
                    execution_result_json=record.execution_result,
                )
            )

    def get(self, case_id: str) -> CaseRecord | None:
        with get_engine().connect() as conn:
            row = conn.execute(select(cases).where(cases.c.case_id == case_id)).mappings().first()
        if not row:
            return None
        analysis = AnalysisResult.model_validate(row["analysis_json"]) if row["analysis_json"] else None
        return CaseRecord(
            case_id=row["case_id"],
            document_text=row["document_text"],
            source=row["source"],
            status=CaseStatus(row["status"]),
            analysis=analysis,
            execution_result=row["execution_result_json"],
        )

    def claim_execution(self, case_id: str | None = None) -> CaseRecord | None:
        with get_engine().begin() as conn:
            stmt = select(cases).where(cases.c.status == CaseStatus.EXECUTION_QUEUED.value)
            if case_id:
                stmt = stmt.where(cases.c.case_id == case_id)
            stmt = stmt.order_by(cases.c.case_id).limit(1)
            if conn.dialect.name == "postgresql":
                stmt = stmt.with_for_update(skip_locked=True)
            row = conn.execute(stmt).mappings().first()
            if not row:
                return None
            conn.execute(update(cases).where(cases.c.case_id == row["case_id"]).values(status=CaseStatus.EXECUTING.value))
        record = self.get(row["case_id"])
        return record

    def event(self, record: CaseRecord, event: str, detail: str) -> None:
        with get_engine().begin() as conn:
            conn.execute(insert(audit_events).values(
                case_id=record.case_id,
                event=event,
                detail=detail,
                created_at=now(),
            ))

    def audit(self, case_id: str) -> list[AuditEvent]:
        with get_engine().connect() as conn:
            rows = conn.execute(
                select(audit_events)
                .where(audit_events.c.case_id == case_id)
                .order_by(audit_events.c.event_id)
            ).mappings().all()
        return [AuditEvent(
            event=row["event"],
            detail=row["detail"],
            created_at=row["created_at"],
        ) for row in rows]

    def record_usage(self, case_id: str, input_tokens: int, output_tokens: int, cost: float) -> None:
        with get_engine().begin() as conn:
            conn.execute(insert(metrics_ledger).values(
                case_id=case_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                estimated_cost_usd=cost,
            ))

    def metrics(self) -> Metrics:
        with get_engine().connect() as conn:
            total = conn.execute(select(func.count()).select_from(cases)).scalar_one()
            rows = conn.execute(select(cases.c.status, func.count()).group_by(cases.c.status)).all()
            usage = conn.execute(select(
                func.coalesce(func.sum(metrics_ledger.c.input_tokens), 0),
                func.coalesce(func.sum(metrics_ledger.c.output_tokens), 0),
                func.coalesce(func.sum(metrics_ledger.c.estimated_cost_usd), 0.0),
            )).one()
        by_status = {str(status): int(count) for status, count in rows}
        return Metrics(
            total_cases=int(total),
            by_status=by_status,
            total_input_tokens=int(usage[0]),
            total_output_tokens=int(usage[1]),
            estimated_cost_usd=round(float(usage[2]), 6),
            execution_queue_depth=by_status.get(CaseStatus.EXECUTION_QUEUED.value, 0),
            review_required_count=by_status.get(CaseStatus.REVIEW_REQUIRED.value, 0),
        )

    def clear(self) -> None:
        with get_engine().begin() as conn:
            conn.execute(delete(audit_events))
            conn.execute(delete(metrics_ledger))
            conn.execute(delete(cases))


store = SqlCaseStore()

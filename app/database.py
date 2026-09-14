import os

from sqlalchemy import JSON, Column, Float, Integer, MetaData, String, Table, Text, create_engine

metadata = MetaData()

cases = Table(
    "cases",
    metadata,
    Column("case_id", String(64), primary_key=True),
    Column("document_text", Text, nullable=False),
    Column("source", String(50), nullable=False),
    Column("status", String(50), nullable=False),
    Column("analysis_json", JSON, nullable=True),
    Column("execution_result_json", JSON, nullable=True),
)

audit_events = Table(
    "audit_events",
    metadata,
    Column("event_id", Integer, primary_key=True, autoincrement=True),
    Column("case_id", String(64), nullable=False, index=True),
    Column("event", String(100), nullable=False),
    Column("detail", Text, nullable=False),
    Column("created_at", String(64), nullable=False),
)

metrics_ledger = Table(
    "metrics_ledger",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("case_id", String(64), nullable=False, index=True),
    Column("input_tokens", Integer, nullable=False),
    Column("output_tokens", Integer, nullable=False),
    Column("estimated_cost_usd", Float, nullable=False),
)

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        url = os.getenv("CASE_DATABASE_URL")
        if not url:
            url = f"sqlite:///{os.getenv('CASE_DB_PATH', 'intelligent_automation.db')}"
        _engine = create_engine(url, future=True)
        metadata.create_all(_engine)
    return _engine

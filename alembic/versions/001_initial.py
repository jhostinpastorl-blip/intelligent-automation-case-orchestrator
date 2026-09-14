from alembic import op
import sqlalchemy as sa
revision="001"
down_revision=None
branch_labels=None
depends_on=None
def upgrade():
    op.create_table("cases",sa.Column("case_id",sa.String(64),primary_key=True),sa.Column("document_text",sa.Text(),nullable=False),sa.Column("source",sa.String(50),nullable=False),sa.Column("status",sa.String(50),nullable=False),sa.Column("analysis_json",sa.JSON(),nullable=True),sa.Column("execution_result_json",sa.JSON(),nullable=True))
    op.create_table("audit_events",sa.Column("event_id",sa.Integer(),primary_key=True,autoincrement=True),sa.Column("case_id",sa.String(64),nullable=False),sa.Column("event",sa.String(100),nullable=False),sa.Column("detail",sa.Text(),nullable=False),sa.Column("created_at",sa.String(64),nullable=False))
    op.create_index("ix_audit_events_case_id","audit_events",["case_id"])
    op.create_table("metrics_ledger",sa.Column("id",sa.Integer(),primary_key=True,autoincrement=True),sa.Column("case_id",sa.String(64),nullable=False),sa.Column("input_tokens",sa.Integer(),nullable=False),sa.Column("output_tokens",sa.Integer(),nullable=False),sa.Column("estimated_cost_usd",sa.Float(),nullable=False))
    op.create_index("ix_metrics_ledger_case_id","metrics_ledger",["case_id"])
def downgrade():
    op.drop_index("ix_metrics_ledger_case_id",table_name="metrics_ledger"); op.drop_table("metrics_ledger"); op.drop_index("ix_audit_events_case_id",table_name="audit_events"); op.drop_table("audit_events"); op.drop_table("cases")

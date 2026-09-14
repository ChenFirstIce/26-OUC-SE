"""Add C/B assisted-task result layers and interview evidence."""
from alembic import op
import sqlalchemy as sa

revision = "20260914_02"
down_revision = "20260910_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    tables = set(inspector.get_table_names())
    # Some historical questionnaire-only databases intentionally omit patient workflow tables.
    if not {"assessments", "assignment_items"} <= tables:
        return
    columns = {column["name"] for column in inspector.get_columns("assessments")}
    with op.batch_alter_table("assessments") as batch:
        for name in ("auto_result_json", "candidate_result_json", "final_result_json"):
            if name not in columns:
                batch.add_column(sa.Column(name, sa.JSON(), nullable=False, server_default="{}"))
    if "llm_sessions" not in tables:
        op.create_table("llm_sessions", sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("assignment_item_id", sa.Integer(), sa.ForeignKey("assignment_items.id"), nullable=False),
            sa.Column("external_session_id", sa.String(100), nullable=False),
            sa.Column("progress", sa.Integer(), nullable=False, server_default="15"),
            sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("assignment_item_id", "external_session_id", name="uq_llm_item_session"))
        op.create_index("ix_llm_sessions_assignment_item_id", "llm_sessions", ["assignment_item_id"])
    if "llm_messages" not in tables:
        op.create_table("llm_messages", sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("session_id", sa.Integer(), sa.ForeignKey("llm_sessions.id"), nullable=False),
            sa.Column("role", sa.String(16), nullable=False), sa.Column("content", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False))
        op.create_index("ix_llm_messages_session_id", "llm_messages", ["session_id"])


def downgrade() -> None:
    op.drop_table("llm_messages")
    op.drop_table("llm_sessions")
    with op.batch_alter_table("assessments") as batch:
        for name in ("final_result_json", "candidate_result_json", "auto_result_json"):
            batch.drop_column(name)

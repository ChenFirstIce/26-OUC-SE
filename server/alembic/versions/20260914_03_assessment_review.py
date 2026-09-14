"""Add clinician review workflow and append-only review history."""
from alembic import op
import sqlalchemy as sa

revision = "20260914_03"
down_revision = "20260914_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    tables = set(inspector.get_table_names())
    if "assessments" not in tables:
        return
    columns = {column["name"] for column in inspector.get_columns("assessments")}
    with op.batch_alter_table("assessments") as batch:
        if "review_note" not in columns:
            batch.add_column(sa.Column("review_note", sa.Text(), nullable=False, server_default=""))
        if "reviewed_by_id" not in columns:
            batch.add_column(sa.Column("reviewed_by_id", sa.Integer(),
                                       sa.ForeignKey("users.id", name="fk_assessments_reviewed_by_id_users"), nullable=True))
        if "reviewed_at" not in columns:
            batch.add_column(sa.Column("reviewed_at", sa.DateTime(), nullable=True))
    if "assessment_review_events" not in tables:
        op.create_table(
            "assessment_review_events",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("assessment_id", sa.Integer(), nullable=True),
            sa.Column("assignment_item_id", sa.Integer(), sa.ForeignKey("assignment_items.id"), nullable=False),
            sa.Column("reviewer_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("action", sa.String(20), nullable=False),
            sa.Column("note", sa.Text(), nullable=False, server_default=""),
            sa.Column("snapshot_json", sa.JSON(), nullable=False, server_default="{}"),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )
        for column in ("assessment_id", "assignment_item_id", "reviewer_id", "action", "created_at"):
            op.create_index(f"ix_assessment_review_events_{column}", "assessment_review_events", [column])


def downgrade() -> None:
    op.drop_table("assessment_review_events")
    with op.batch_alter_table("assessments") as batch:
        batch.drop_column("reviewed_at")
        batch.drop_column("reviewed_by_id")
        batch.drop_column("review_note")

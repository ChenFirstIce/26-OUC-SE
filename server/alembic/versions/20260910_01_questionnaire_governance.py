"""Add version-level questionnaire governance fields.

Revision ID: 20260910_01
Revises:
Create Date: 2026-09-10
"""
from alembic import op
import sqlalchemy as sa


revision = "20260910_01"
down_revision = None
branch_labels = None
depends_on = None


NEW_COLUMNS = {
    "name": sa.Column("name", sa.String(length=120), nullable=True),
    "description": sa.Column("description", sa.Text(), nullable=True),
    "status": sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
    "content_hash": sa.Column("content_hash", sa.String(length=64), nullable=True),
    "change_summary": sa.Column("change_summary", sa.Text(), nullable=False, server_default=""),
    "created_by_id": sa.Column("created_by_id", sa.Integer(), nullable=True),
    "created_at": sa.Column("created_at", sa.DateTime(), nullable=True),
    "published_by_id": sa.Column("published_by_id", sa.Integer(), nullable=True),
    "retired_at": sa.Column("retired_at", sa.DateTime(), nullable=True),
    "retired_by_id": sa.Column("retired_by_id", sa.Integer(), nullable=True),
    "retirement_reason": sa.Column("retirement_reason", sa.Text(), nullable=False, server_default=""),
}


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing = {column["name"] for column in inspector.get_columns("questionnaire_versions")}
    with op.batch_alter_table("questionnaire_versions") as batch:
        for name, column in NEW_COLUMNS.items():
            if name not in existing:
                batch.add_column(column)

    connection.execute(sa.text("""
        UPDATE questionnaire_versions
        SET name = COALESCE(name, (SELECT name FROM questionnaire_templates WHERE id = questionnaire_versions.template_id)),
            description = COALESCE(description, (SELECT description FROM questionnaire_templates WHERE id = questionnaire_versions.template_id)),
            created_at = COALESCE(created_at, published_at, CURRENT_TIMESTAMP),
            status = CASE WHEN published_at IS NULL THEN 'draft' ELSE 'retired' END
    """))
    connection.execute(sa.text("""
        UPDATE questionnaire_versions
        SET status = 'published'
        WHERE id IN (
            SELECT qv.id FROM questionnaire_versions qv
            WHERE qv.published_at IS NOT NULL
              AND qv.version = (
                  SELECT MAX(qv2.version) FROM questionnaire_versions qv2
                  WHERE qv2.template_id = qv.template_id AND qv2.published_at IS NOT NULL
              )
        )
    """))
    connection.execute(sa.text("""
        UPDATE questionnaire_templates
        SET status = CASE
            WHEN EXISTS (SELECT 1 FROM questionnaire_versions qv WHERE qv.template_id = questionnaire_templates.id AND qv.status = 'published') THEN 'published'
            WHEN EXISTS (SELECT 1 FROM questionnaire_versions qv WHERE qv.template_id = questionnaire_templates.id AND qv.status = 'draft') THEN 'draft'
            ELSE 'retired'
        END
    """))


def downgrade() -> None:
    existing = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("questionnaire_versions")}
    with op.batch_alter_table("questionnaire_versions") as batch:
        for name in reversed(list(NEW_COLUMNS)):
            if name in existing:
                batch.drop_column(name)

"""Add encrypted LLM provider configuration."""
from alembic import op
import sqlalchemy as sa

revision = "20260915_04"
down_revision = "20260914_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    tables = set(inspector.get_table_names())
    if "llm_provider_configs" in tables:
        return
    op.create_table(
        "llm_provider_configs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("encrypted_api_key", sa.Text(), nullable=True),
        sa.Column("key_hint", sa.String(40), nullable=False, server_default=""),
        sa.Column("model", sa.String(80), nullable=False, server_default="deepseek-flash"),
        sa.Column("base_url", sa.String(255), nullable=False, server_default="https://api.deepseek.com"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("updated_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("provider", name="uq_llm_provider_configs_provider"),
    )
    op.create_index("ix_llm_provider_configs_provider", "llm_provider_configs", ["provider"])
    op.create_index("ix_llm_provider_configs_enabled", "llm_provider_configs", ["enabled"])


def downgrade() -> None:
    op.drop_table("llm_provider_configs")

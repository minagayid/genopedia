"""Create account and revocable session tables."""
from alembic import op
import sqlalchemy as sa
revision = "0001_users_and_sessions"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("users", sa.Column("id", sa.String(36), nullable=False), sa.Column("email", sa.String(254), nullable=False), sa.Column("display_name", sa.String(80), nullable=False), sa.Column("password_hash", sa.String(255), nullable=False), sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table("user_sessions", sa.Column("id", sa.String(36), nullable=False), sa.Column("user_id", sa.String(36), nullable=False), sa.Column("token_hash", sa.String(64), nullable=False), sa.Column("csrf_token_hash", sa.String(64), nullable=False), sa.Column("created_at", sa.BigInteger(), nullable=False), sa.Column("expires_at", sa.BigInteger(), nullable=False), sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"), sa.PrimaryKeyConstraint("id"))
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"], unique=False)
    op.create_index("ix_user_sessions_token_hash", "user_sessions", ["token_hash"], unique=True)
    op.create_index("ix_user_sessions_expires_at", "user_sessions", ["expires_at"], unique=False)

def downgrade() -> None:
    op.drop_index("ix_user_sessions_expires_at", table_name="user_sessions")
    op.drop_index("ix_user_sessions_token_hash", table_name="user_sessions")
    op.drop_index("ix_user_sessions_user_id", table_name="user_sessions")
    op.drop_table("user_sessions")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

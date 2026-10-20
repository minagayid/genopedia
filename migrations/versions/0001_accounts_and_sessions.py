from alembic import op
import sqlalchemy as sa
revision="0001_accounts"
down_revision=None
branch_labels=None
depends_on=None
def upgrade():
 op.create_table("users",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("email",sa.String(320),nullable=False),sa.Column("full_name",sa.String(120)),sa.Column("password_hash",sa.String(512)),sa.Column("email_verified",sa.Boolean(),nullable=False,server_default=sa.false()),sa.Column("is_active",sa.Boolean(),nullable=False,server_default=sa.true()),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False))
 op.create_index("ix_users_email","users",["email"],unique=True)
 op.create_table("refresh_sessions",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("user_id",sa.Integer(),sa.ForeignKey("users.id",ondelete="CASCADE"),nullable=False),sa.Column("token_hash",sa.String(64),nullable=False),sa.Column("expires_at",sa.DateTime(timezone=True),nullable=False),sa.Column("revoked_at",sa.DateTime(timezone=True)),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("user_agent",sa.String(512)),sa.UniqueConstraint("token_hash",name="uq_refresh_token_hash"))
 op.create_index("ix_refresh_sessions_user_id","refresh_sessions",["user_id"])
 op.create_table("audit_events",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("user_id",sa.Integer(),sa.ForeignKey("users.id",ondelete="SET NULL")),sa.Column("event_type",sa.String(80),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("details",sa.Text()))
 op.create_index("ix_audit_events_user_id","audit_events",["user_id"]);op.create_index("ix_audit_events_event_type","audit_events",["event_type"])
def downgrade():
 op.drop_index("ix_audit_events_event_type",table_name="audit_events");op.drop_index("ix_audit_events_user_id",table_name="audit_events");op.drop_table("audit_events")
 op.drop_index("ix_refresh_sessions_user_id",table_name="refresh_sessions");op.drop_table("refresh_sessions");op.drop_index("ix_users_email",table_name="users");op.drop_table("users")

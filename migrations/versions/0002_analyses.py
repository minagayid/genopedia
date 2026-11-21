from alembic import op
import sqlalchemy as sa
revision="0002_analyses"
down_revision="0001_accounts"
branch_labels=None
depends_on=None
def upgrade():
 op.create_table("analyses",sa.Column("id",sa.Integer(),primary_key=True),sa.Column("user_id",sa.Integer(),sa.ForeignKey("users.id",ondelete="CASCADE"),nullable=False),sa.Column("name",sa.String(200),nullable=False),sa.Column("input_format",sa.String(20),nullable=False),sa.Column("molecule",sa.String(10),nullable=False),sa.Column("record_count",sa.Integer(),nullable=False),sa.Column("variant_count",sa.Integer(),nullable=False),sa.Column("total_bases",sa.Integer(),nullable=False),sa.Column("sequence_sha256",sa.String(64),nullable=False),sa.Column("summary_json",sa.Text(),nullable=False),sa.Column("report_html",sa.Text(),nullable=False),sa.Column("records_json",sa.Text(),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
 op.create_index("ix_analyses_user_id","analyses",["user_id"])
def downgrade():
 op.drop_index("ix_analyses_user_id",table_name="analyses");op.drop_table("analyses")

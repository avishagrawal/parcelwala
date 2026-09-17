"""create auth tables

Revision ID: 0001_auth
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_auth"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("roles", sa.Column("id", sa.String(36), primary_key=True), sa.Column("name", sa.String(50), nullable=False, unique=True), sa.Column("description", sa.String(255)))
    op.create_index("ix_roles_name", "roles", ["name"], unique=False)
    op.create_table("permissions", sa.Column("id", sa.String(36), primary_key=True), sa.Column("name", sa.String(100), nullable=False, unique=True), sa.Column("description", sa.String(255)))
    op.create_table("users", sa.Column("id", sa.String(36), primary_key=True), sa.Column("email", sa.String(255), nullable=False, unique=True), sa.Column("full_name", sa.String(160), nullable=False), sa.Column("password_hash", sa.String(255), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_users_email", "users", ["email"], unique=False)
    op.create_table("user_roles", sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True), sa.Column("role_id", sa.String(36), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True))
    op.create_table("role_permissions", sa.Column("role_id", sa.String(36), sa.ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True), sa.Column("permission_id", sa.String(36), sa.ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True))
    op.create_table("refresh_tokens", sa.Column("id", sa.String(36), primary_key=True), sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False), sa.Column("token_id", sa.String(36), nullable=False, unique=True), sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False), sa.Column("revoked", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_id", "refresh_tokens", ["token_id"])
    op.create_table("audit_logs", sa.Column("id", sa.String(36), primary_key=True), sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL")), sa.Column("action", sa.String(100), nullable=False), sa.Column("details", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))

def downgrade():
    for table in ["audit_logs", "refresh_tokens", "role_permissions", "user_roles", "users", "permissions", "roles"]: op.drop_table(table)

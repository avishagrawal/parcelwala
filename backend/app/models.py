import uuid
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Table, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from .database import Base, utcnow

user_roles = Table("user_roles", Base.metadata,
    Column("user_id", String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", String(36), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
)
role_permissions = Table("role_permissions", Base.metadata,
    Column("role_id", String(36), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", String(36), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)

class TimestampMixin:
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

class User(TimestampMixin, Base):
    __tablename__ = "users"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(160), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    roles = relationship("Role", secondary=user_roles, back_populates="users", lazy="selectin")

class Role(Base):
    __tablename__ = "roles"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")

class Permission(Base):
    __tablename__ = "permissions"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_id = Column(String(36), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)

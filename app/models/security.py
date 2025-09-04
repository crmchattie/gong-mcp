import enum
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, func
from sqlalchemy.orm import relationship
from app.database import Base


class UserStatusEnum(str, enum.Enum):
    FREE = "FREE"
    BLOCKED = "BLOCKED"


class TierEnum(str, enum.Enum):
    ENTERPRISE = "ENTERPRISE"
    TRIAL = "TRIAL"
    FREE = "FREE"
    STUDENT = "STUDENT"


class MCPUserActivity(Base):
    __tablename__ = "mcp_user_activity"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("mcp_user.id", ondelete="CASCADE"))
    accessed_company = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("MCPUser", back_populates="activities")


class MCPUser(Base):
    __tablename__ = "mcp_user"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    tier = Column(Enum(TierEnum), default=TierEnum.TRIAL, nullable=False)
    total_limit = Column(Integer, nullable=False)
    status = Column(Enum(UserStatusEnum), default=UserStatusEnum.FREE, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    unblocked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    blocked_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    activities = relationship("MCPUserActivity", back_populates="user")

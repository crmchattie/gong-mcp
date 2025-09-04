from sqlalchemy import Column, DateTime, Integer, String, JSON
from sqlalchemy.sql import func
from app.database import Base


class OAuthUserMCP(Base):
    __tablename__ = "oauth_user_mcp"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(255), index=True)
    client_secret = Column(String(255), index=True)
    client_name = Column(String(255), index=True)
    redirect_uris = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<OAuthUserMCP(id={self.id}, client_id={self.client_id}, client_name={self.client_name})>"

from sqlalchemy import Column, String, Integer
from app.database import Base
from sqlalchemy.orm import relationship


class AuthGroup(Base):
    __tablename__ = "auth_group"

    id = Column(Integer, primary_key=True)
    name = Column(String(150), unique=True, nullable=False, index=True)
    users = relationship("UserGroups", back_populates="group")

    def __repr__(self):
        return f"<AuthGroup(id={self.id}, name={self.name})>"


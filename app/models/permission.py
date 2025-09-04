from sqlalchemy import Column, String, Integer
from app.database import Base
from sqlalchemy.orm import relationship


class Permission(Base):
    __tablename__ = "auth_permission"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    codename = Column(String(100), unique=True, nullable=False, index=True)
    users = relationship("UserPermissions", back_populates="permission")

    def __repr__(self):
        return f"<Permission(id={self.id}, name={self.name}, codename={self.codename})>"

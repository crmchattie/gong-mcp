from sqlalchemy import Boolean, Column, ForeignKey, String, Integer
from sqlalchemy.orm import relationship
from passlib.hash import django_pbkdf2_sha256
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password = Column(String(128), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    groups = relationship("UserGroups", back_populates="user")
    permissions = relationship("UserPermissions", back_populates="user")
    api_keys = relationship("APIKey", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"

    def check_password(self, raw_password: str) -> bool:
        """
        Verifies `raw_password` against the stored hash.
        Returns True if it matches, False otherwise.
        """
        return django_pbkdf2_sha256.verify(raw_password, self.password)


class UserGroups(Base):
    __tablename__ = "users_groups"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    group_id = Column(Integer, ForeignKey("auth_group.id", ondelete="CASCADE"))

    user = relationship("User", back_populates="groups")
    group = relationship("AuthGroup", back_populates="users")

    def __repr__(self):
        return f"<UserGroups(user_id={self.user_id}, group_id={self.group_id})>"


class UserPermissions(Base):
    __tablename__ = "users_user_permissions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    permission_id = Column(Integer, ForeignKey("auth_permission.id", ondelete="CASCADE"))

    user = relationship("User", back_populates="permissions")
    permission = relationship("Permission", back_populates="users")

    def __repr__(self):
        return f"<UserPermissions(user_id={self.user_id}, permission_id={self.permission_id})>"

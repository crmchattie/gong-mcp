from app.models.user import User, UserGroups, UserPermissions
from app.models.group import AuthGroup
from app.models.permission import Permission
from app.models.apikey import APIKey
from sqlalchemy import exists, join, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.default_tier = "enterprise"
    
    async def validate_password(self, email: str, password: str) -> bool:
        """
        Validate user credentials with email and password.
        Returns True if the user exists and the password is correct, otherwise False.
        """

        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user or not user.check_password(password):
            return False
        return True
    
    async def get_user_tier(self, email: str) -> str:
        """
        Retrieve the tier of the user based on their email.
        Returns None if the user does not exist.
        """
        user = await self.get_user_with_groups(email)
        if not user:
            return self.default_tier
        
        user_groups = [auth_group.group.name for auth_group in user.groups]
        for group in user_groups:
            if group.startswith("user_type:"):
                user_type = group.replace("user_type:", "")

        if user_type == "enterprise_trial":
            return "trial"
        elif user_type == "student":
            return "student"
        elif user_type == "free":
            return "free"
        else:
            return self.default_tier

    async def get_user_with_groups(self, email: str) -> User | None:
        """
        Retrieve user for email along with their groups.
        """
        stmt = (
            select(User)
            .options(
                selectinload(User.groups).selectinload(UserGroups.group)
            )
            .where(User.email == email)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def has_mcp_access(self, email: str) -> bool:
        """
        Check if the user has MCP access based on permissions.
        Returns True if the user has access, otherwise False.
        """
        stmt = (
            select(
                exists().where(
                    User.email == email,
                    User.is_active == True,
                    User.id == UserPermissions.user_id,
                    UserPermissions.permission_id == Permission.id,
                    Permission.codename == "has_mcp_access"
                )
            )
        )
        
        result = await self.db.execute(stmt)
        return result.scalar()

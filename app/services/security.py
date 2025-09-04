from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import exists
from datetime import datetime, timedelta

from starlette.requests import Request

from app.constants import TIER_TIME_LIMITS, TIER_TOTAL_LIMITS
from app.models.security import MCPUser, MCPUserActivity, UserStatusEnum


class MCPSecurityService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_or_create_mcp_user(self, email: str, tier: str) -> MCPUser | None:
        user = await self._get_mcp_user(email)
        if user is None:
            user = await self._create_mcp_user(email, tier)
        return user

    async def _get_mcp_user(self, email: str) -> MCPUser | None:
        stmt = select(MCPUser).where(MCPUser.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _create_mcp_user(self, email: str, tier: str) -> MCPUser | None:
        total_limit = TIER_TOTAL_LIMITS.get(tier.upper(), 10)
        reference_date = datetime.now()
        user = MCPUser(
            email=email,
            tier=tier.upper(),
            total_limit=total_limit,
            created_at=reference_date,
            unblocked_at=reference_date,
            blocked_at=reference_date,
        )
        self.db.add(user)
        try:
            await self.db.commit()
            return user
        except IntegrityError:
            await self.db.rollback()
            return None

    async def access_control(self, user: MCPUser, company_id: int) -> tuple[bool, str]:
        tier_config = TIER_TIME_LIMITS[user.tier]
        limit = tier_config["limit"]
        days = tier_config["days"]

        if user.email.endswith("@daloopa.com"):
            return True, "Access granted for internal Daloopa users."

        if await self.is_total_limit_reached(user):
            return False, "Total limit reached for the user."

        if await self._should_auto_unblock(user, days):
            await self._unblock_user(user)

        if await self._already_accessed_company(user.id, company_id):
            return True, ""
        
        if user.status == UserStatusEnum.BLOCKED:
            unblock_time = (user.unblocked_at + timedelta(days=days)).strftime("%Y-%m-%d %H:%M")
            return False, f"User is blocked. Limit will be reset automatically at {unblock_time} UTC."

        if await self._is_limit_reached(user.id, user.unblocked_at, days, limit):
            await self._block_user(user)
            unblock_time = (user.unblocked_at + timedelta(days=days)).strftime("%Y-%m-%d %H:%M")
            return False, f"User is blocked. Limit will be reset automatically at {unblock_time} UTC."

        await self._log_access(user.id, company_id)
        return True, ""

    async def _should_auto_unblock(self, user: MCPUser, days: int) -> bool:
        if user.status != UserStatusEnum.BLOCKED:
            return False

        time_since_unblock = datetime.now() - user.unblocked_at
        return time_since_unblock.days >= days

    async def _unblock_user(self, user: MCPUser):
        user.status = UserStatusEnum.FREE
        user.unblocked_at = datetime.now()
        await self.db.commit()

    async def _block_user(self, user: MCPUser):
        user.status = UserStatusEnum.BLOCKED
        user.blocked_at = datetime.now()
        await self.db.commit()

    async def _log_access(self, user_id: int, company_id: int):
        self.db.add(MCPUserActivity(user_id=user_id, accessed_company=company_id, timestamp=datetime.now()))
        await self.db.commit()

    async def _already_accessed_company(self, user_id: int, company_id: int) -> bool:
        result = await self.db.execute(
            select(MCPUserActivity.id)
            .where(
                MCPUserActivity.user_id == user_id,
                MCPUserActivity.accessed_company == company_id,
            )
            .limit(1)
        )

        return result.scalar_one_or_none() is not None

    async def _is_limit_reached(self, user_id: int, unblock_time: datetime, days: int, limit: int) -> bool:
        window_start = max(unblock_time, datetime.now() - timedelta(days=days))
        result = await self.db.execute(
            select(func.count(distinct(MCPUserActivity.accessed_company)))
            .where(
                MCPUserActivity.user_id == user_id,
                MCPUserActivity.timestamp >= window_start
            )
        )
        count = result.scalar_one()
        return count >= limit

    async def is_total_limit_reached(self, user: MCPUser) -> bool:
        total_limit = user.total_limit
        result = await self.db.execute(
            select(func.count(distinct(MCPUserActivity.accessed_company)))
            .where(MCPUserActivity.user_id == user.id)
        )
        count = result.scalar_one()
        return count >= total_limit

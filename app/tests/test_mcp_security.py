import pytest
from sqlalchemy import select
from datetime import datetime, timedelta
from freezegun import freeze_time

from app.constants import TIER_TIME_LIMITS, TIER_TOTAL_LIMITS
from app.models.security import MCPUser, MCPUserActivity, UserStatusEnum
from app.models.user import UserPermissions
from app.services.security import MCPSecurityService
from app.services.user import UserService


@pytest.mark.asyncio
class TestMCPUser:
    async def test_base_user_creation(self, async_session):
        email = "test@example.com"
        tier = "ENTERPRISE"
        service = MCPSecurityService(async_session)
        user = await service.get_or_create_mcp_user(email, tier)

        assert user.id is not None
        assert user.email == email
        assert user.tier == tier
        assert user.status == "FREE"
        assert user.total_limit == TIER_TOTAL_LIMITS[tier]


@pytest.mark.asyncio
class TestUserActivity:
    async def test_should_auto_unblock_true(self, async_session, free_mcp_user):
        # User was created and blocked 1 day later and enough days passed
        user = free_mcp_user
        tier = user.tier
        days = TIER_TIME_LIMITS[tier]["days"]
        
        created_at = datetime.now() - timedelta(days=days + 2)
        unblocked_at = datetime.now() - timedelta(days=days + 2)
        blocked_at = datetime.now() - timedelta(days=days + 1)

        user.status = UserStatusEnum.BLOCKED
        user.created_at = created_at
        user.unblocked_at = unblocked_at
        user.blocked_at = blocked_at
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        service = MCPSecurityService(async_session)
        assert await service._should_auto_unblock(user, days=days) is True

    async def test_should_auto_unblock_false(self, async_session, free_mcp_user):
        # User was created and blocked 1 day later, but not enough days passed
        user = free_mcp_user
        tier = user.tier
        days = TIER_TIME_LIMITS[tier]["days"]
        
        created_at = datetime.now() - timedelta(days=days - 1)
        unblocked_at = datetime.now() - timedelta(days=days - 1)
        blocked_at = datetime.now() - timedelta(days=days - 2)

        user.status = UserStatusEnum.BLOCKED
        user.created_at = created_at
        user.unblocked_at = unblocked_at
        user.blocked_at = blocked_at
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        service = MCPSecurityService(async_session)
        assert await service._should_auto_unblock(user, days=days) is False

    async def test_block_and_unblock_user(self, async_session, free_mcp_user):
        user = free_mcp_user
        service = MCPSecurityService(async_session)
        await service._block_user(user)
        assert user.status == UserStatusEnum.BLOCKED

        await service._unblock_user(user)
        assert user.status == UserStatusEnum.FREE

    async def test_log_and_check_access(self, async_session, free_mcp_user):
        user = free_mcp_user
        service = MCPSecurityService(async_session)
        assert await service._already_accessed_company(user.id, company_id=1) is False
        await service._log_access(user.id, company_id=1)
        assert await service._already_accessed_company(user.id, company_id=1) is True

    async def test_is_limit_reached(self, async_session, free_mcp_user):
        user = free_mcp_user
        service = MCPSecurityService(async_session)

        time_limit = TIER_TIME_LIMITS[user.tier]["limit"]
        days_limit = TIER_TIME_LIMITS[user.tier]["days"]
        for i in range(time_limit - 1):
            await service._log_access(user.id, company_id=i)
        limit_reached = await service._is_limit_reached(
            user_id=user.id,
            unblock_time=user.unblocked_at,
            days=days_limit,
            limit=time_limit,
        )
        assert limit_reached is False

        await service._log_access(user.id, company_id=99)
        limit_reached = await service._is_limit_reached(
            user_id=user.id,
            unblock_time=user.unblocked_at,
            days=days_limit,
            limit=time_limit,
        )
        assert limit_reached is True

    async def test_is_total_limit_reached(self, async_session, free_mcp_user):
        user = free_mcp_user
        total_limit = user.total_limit
        service = MCPSecurityService(async_session)

        for company_id in range(total_limit - 1):
            await service._log_access(user.id, company_id=company_id)
        assert await service.is_total_limit_reached(user) is False
        await service._log_access(user.id, company_id=total_limit)
        assert await service.is_total_limit_reached(user) is True
    
    async def test_full_flow(self, async_session, free_mcp_user):
        user = free_mcp_user
        service = MCPSecurityService(async_session)
        user.total_limit = 999
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        time_limit = TIER_TIME_LIMITS[user.tier]["limit"]
        days_limit = TIER_TIME_LIMITS[user.tier]["days"]

        # Simulate accesses over `days_limit` (1 access per day)
        for i in range(time_limit):
            with freeze_time(datetime.now() - timedelta(days=days_limit - i)):
                user_can_access, _ = await service.access_control(user, company_id=i)
                assert user_can_access is True

        # Now simulate spamming `time_limit` accesses again quickly (within minutes)
        range_max = min(time_limit * 2, time_limit + days_limit)
        for i in range(time_limit, range_max + 1):
            user_can_access, message = await service.access_control(user, company_id=i)
            if i == range_max:
                assert user_can_access is False and "User is blocked" in message
            else:
                assert user_can_access is True

        await async_session.refresh(user)
        assert user.status == UserStatusEnum.BLOCKED

        # Advance time to allow auto-unblock
        unblock_at = user.unblocked_at + timedelta(days=days_limit)
        with freeze_time(unblock_at + timedelta(minutes=1)):
            # First attempt triggers auto-unblock
            user_can_access, _ = await service.access_control(user, company_id=range_max + 1)
            assert user_can_access is True
            assert user.status == UserStatusEnum.FREE

        # Continue accessing until total limit is reached
        already_accessed = await async_session.execute(
            select(MCPUserActivity.accessed_company).where(MCPUserActivity.user_id == user.id)
        )
        accessed_ids = set(row[0] for row in already_accessed)
        number_of_accesses = len(accessed_ids)
        user.total_limit = number_of_accesses + 1
        async_session.add(user)
        await async_session.commit()
        await async_session.refresh(user)

        user_can_access, _ = await service.access_control(user, company_id=number_of_accesses + 1)
        assert user_can_access is True
        
        user_can_access, message = await service.access_control(user, company_id=number_of_accesses + 2)
        assert user_can_access is False
        assert "Total limit reached" in message


@pytest.mark.asyncio
class TestUserPermissions:
    async def test_invalid_user(self, async_session):
        email = "random@random.com"
        has_mcp_access = await UserService(async_session).has_mcp_access(email)
        assert has_mcp_access is False
    
    async def test_mcp_disabled_enabled(self, async_session, test_user, mcp_permission):
        email = test_user.email
        has_mcp_access = await UserService(async_session).has_mcp_access(email)
        assert has_mcp_access is False

        # Enable MCP access
        user_permission = UserPermissions(
            user_id=test_user.id,
            permission_id=mcp_permission.id
        )
        async_session.add(user_permission)
        await async_session.commit()
        await async_session.refresh(test_user)

        has_mcp_access = await UserService(async_session).has_mcp_access(email)
        assert has_mcp_access is True

        # Disable MCP access
        await async_session.delete(user_permission)
        await async_session.commit()
        await async_session.refresh(test_user)

        has_mcp_access = await UserService(async_session).has_mcp_access(email)
        assert has_mcp_access is False

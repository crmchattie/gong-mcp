from sqlalchemy.exc import IntegrityError
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models.permission import Permission
from app.models.user import User
from app.services.security import MCPSecurityService 


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def async_session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def free_mcp_user(async_session):
    email = "test@test.com"
    tier = "FREE"
    service = MCPSecurityService(async_session)
    user = await service.get_or_create_mcp_user(email, tier)
    return user


@pytest_asyncio.fixture
async def test_user(async_session):
    email = "test@test.com"
    user = User(email=email, password="hashed_password")
    async_session.add(user)
    try:
        await async_session.commit()
        return user
    except IntegrityError:
        await async_session.rollback()
        return None


@pytest_asyncio.fixture
async def mcp_permission(async_session):
    codename = "has_mcp_access"
    name = "Has MCP access"
    permission = Permission(codename=codename, name=name)
    async_session.add(permission)
    try:
        await async_session.commit()
        return permission
    except IntegrityError:
        await async_session.rollback()
        return None

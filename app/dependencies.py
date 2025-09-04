from typing import AsyncGenerator
from app.database import DBAsyncSession
from sqlalchemy.ext.asyncio import AsyncSession

# Database Dependency
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with DBAsyncSession() as session:
        yield session

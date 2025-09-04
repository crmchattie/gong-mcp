import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base


DB_USER = os.getenv("DB_USER", "username")
DB_PASS = os.getenv("DB_PASS", "password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "name")
DB_PORT = 3306

# Database (MySQL)
SQLALCHEMY_MYSQL_DATABASE_URL = f"mysql+aiomysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
async_engine = create_async_engine(SQLALCHEMY_MYSQL_DATABASE_URL)
DBAsyncSession = async_sessionmaker(autocommit=False, bind=async_engine, expire_on_commit=False)

Base = declarative_base()

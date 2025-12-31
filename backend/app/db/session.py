from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.variable import SQLALCHEMY_DATABASE_URL_USER


engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL_USER, pool_recycle=3600, pool_pre_ping=True
)

AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

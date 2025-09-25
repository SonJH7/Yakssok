from datetime import date
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user_model import User


class UserService:
    @staticmethod
    async def get_user_by_google_id(google_id: str, db: AsyncSession):
        # 구글아이디로 유저조회
        result = await db.execute(select(User).where(User.user_id == google_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_user(
        google_id: str, email: str, name: str, refresh_token: str, db: AsyncSession
    ):
        # 유저생성
        user = User(
            user_id=google_id,
            email=email,
            name=name,
            google_refresh_token=refresh_token or "",
            created_at=date.today(),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def update_refresh_token(
        user: User, refresh_token: str | None, db: AsyncSession
    ):  # 리프레시토큰 업데이트
        if refresh_token is None or refresh_token == "":
            return

        user.google_refresh_token = refresh_token
        await db.commit()

    @staticmethod
    async def get_or_create_user(
        google_id: str, email: str, name: str, refresh_token: str, db: AsyncSession
    ):
        # 유저 가입여부 확인 및 업데이트
        user = await UserService.get_user_by_google_id(google_id, db)

        if not user:
            user = await UserService.create_user(
                google_id, email, name, refresh_token, db
            )
        else:
            await UserService.update_refresh_token(user, refresh_token, db)

        return user

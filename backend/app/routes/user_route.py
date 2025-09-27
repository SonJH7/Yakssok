from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.google_oauth_service import GoogleOAuthService
from app.services.user_service import UserService
from app.utils.jwt import create_access_token
from app.variable import FRONTEND_URL


security = HTTPBearer()

router = APIRouter(
    prefix="/user",
)


@router.get("/google/login")
async def google_login(force: int | None = None):
    auth_url = GoogleOAuthService.generate_auth_url(force_prompt_consent=bool(force))
    return {"auth_url": auth_url}


@router.get("/callback")
async def google_callback(code: str, db: AsyncSession = Depends(get_db)):
    try:
        # Google OAuth 토큰 교환
        tokens = GoogleOAuthService.exchange_code_for_tokens(code)
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        # 사용자 정보 조회
        user_info = GoogleOAuthService.get_user_info(access_token)
        google_id = user_info["google_id"]
        email = user_info["email"]
        name = user_info["name"]

        # 사용자 조회 또는 생성
        user = await UserService.get_or_create_user(
            google_id, email, name, refresh_token, db
        )

        # JWT 토큰 생성
        jwt_access_token = create_access_token(data={"sub": user.user_id})

        # 프론트엔드로 리디렉션
        redirect_base = FRONTEND_URL.rstrip("/")
        redirect_url = f"{redirect_base}/auth/callback?access_token={jwt_access_token}"
        return RedirectResponse(url=redirect_url, status_code=302)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"로그인 처리 중 오류: {str(e)}")

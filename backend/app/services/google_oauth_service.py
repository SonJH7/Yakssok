import urllib.parse
import requests
from fastapi import HTTPException
from app.variable import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_FORCE_PROMPT_CONSENT,
    GOOGLE_REDIRECT_URI,
)


class GoogleOAuthService:
    @staticmethod
    def generate_auth_url(force_prompt_consent: bool = False):
        # Google OAuth 인증 URL 생성
        scope = (
            "openid email profile " "https://www.googleapis.com/auth/calendar.events"
        )
        params = {
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "scope": scope,
            "response_type": "code",
            "access_type": "offline",
            "include_granted_scopes": "true",
        }
        if GOOGLE_FORCE_PROMPT_CONSENT or force_prompt_consent:
            params["prompt"] = "consent"
        return "https://accounts.google.com/o/oauth2/auth?" + urllib.parse.urlencode(
            params
        )

    @staticmethod
    def exchange_code_for_tokens(code: str):
        # 인증 코드를 액세스 토큰과 리프레시 토큰으로 교환
        token_data = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": GOOGLE_REDIRECT_URI,
        }

        try:
            token_response = requests.post(
                "https://oauth2.googleapis.com/token", data=token_data
            )
            token_response.raise_for_status()
            tokens = token_response.json()

            access_token = tokens.get("access_token")
            refresh_token = tokens.get("refresh_token")

            if not access_token:
                raise HTTPException(status_code=400, detail="토큰을 받을 수 없습니다.")

            return {"access_token": access_token, "refresh_token": refresh_token}
        except requests.RequestException as e:
            raise HTTPException(
                status_code=500, detail=f"구글 토큰 요청 실패: {str(e)}"
            )

    @staticmethod
    def get_user_info(access_token: str):
        # 액세스 토큰으로 사용자 정보 조회
        try:
            user_info_response = requests.get(
                f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={access_token}"
            )
            user_info_response.raise_for_status()
            user_info = user_info_response.json()

            google_id = user_info.get("id")
            email = user_info.get("email")
            name = user_info.get("name")

            if not google_id or not email:
                raise HTTPException(
                    status_code=400, detail="사용자 정보를 가져올 수 없습니다."
                )

            return {"google_id": google_id, "email": email, "name": name}
        except requests.RequestException as e:
            raise HTTPException(
                status_code=500, detail=f"구글 사용자 정보 요청 실패: {str(e)}"
            )

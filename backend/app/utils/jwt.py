from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer
from app.variable import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_current_user(token=Depends(security)):
    # JWT 토큰에서 현재 사용자 정보 추출
    credentials_exception = HTTPException(
        status_code=401,
        detail="인증 정보가 유효하지 않습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = verify_token(token.credentials)
        if payload is None:
            raise credentials_exception
        return payload
    except JWTError:
        raise credentials_exception

import logging

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel

from app.auth import create_session_token, get_current_user
from app.config import settings

logger = logging.getLogger("app.auth")

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(payload: LoginRequest, response: Response):
    if payload.username != settings.admin_username or payload.password != settings.admin_password:
        logger.warning("ログイン失敗: username=%s", payload.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ユーザー名またはパスワードが違います",
        )

    token = create_session_token(payload.username)
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7日
        path="/",
    )
    logger.info("ログイン成功: username=%s", payload.username)
    return {"username": payload.username}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key=settings.session_cookie_name, path="/")
    return {"message": "ログアウトしました"}


@router.get("/me")
def me(username: str = Depends(get_current_user)):
    return {"username": username}

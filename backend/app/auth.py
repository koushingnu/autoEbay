import hashlib
import hmac

from fastapi import Cookie, HTTPException, status

from app.config import settings


def create_session_token(username: str) -> str:
    """ユーザー名を秘密鍵で署名した簡易セッショントークンを作る。"""
    signature = hmac.new(
        settings.session_secret.encode(),
        username.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{username}:{signature}"


def verify_session_token(token: str) -> str | None:
    """トークンを検証し、正当ならユーザー名を返す。不正なら None。"""
    try:
        username, _ = token.split(":", 1)
    except ValueError:
        return None
    expected = create_session_token(username)
    if hmac.compare_digest(expected, token):
        return username
    return None


def get_current_user(ae_session: str | None = Cookie(default=None)) -> str:
    """保護されたエンドポイント用の依存性。未ログインなら 401。"""
    if not ae_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未ログインです")
    username = verify_session_token(ae_session)
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="セッションが無効です")
    return username

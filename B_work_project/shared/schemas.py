from typing import Optional

from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    scope: str
    expires_in: int
    id_token: Optional[str] = None
    refresh_token: Optional[str] = None


class TokenPayload(BaseModel):
    sub: str
    username: str
    role: str
    scope: str
    client_id: str
    exp: int
    iss: Optional[str] = None
    aud: Optional[str] = None
    iat: Optional[int] = None
    jti: Optional[str] = None

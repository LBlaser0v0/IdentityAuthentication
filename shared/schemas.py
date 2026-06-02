from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    scope: str


class TokenPayload(BaseModel):
    sub: str
    username: str
    role: str
    scope: str
    client_id: str
    exp: int

from fastapi import APIRouter, Depends, Header, HTTPException

from resource_server.services import require_role, require_scope
from shared.jwt_utils import decode_access_token

router = APIRouter()


def get_token_payload(authorization: str = Header(default="")):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        return decode_access_token(token)
    except Exception as exc:
        raise HTTPException(status_code=401, detail=f"invalid token: {exc}")


@router.get("/")
def root():
    return {"service": "resource-server", "status": "ok"}


@router.get("/profile")
def profile(payload=Depends(get_token_payload)):
    require_scope(payload.get("scope", ""), "read:profile")
    return {
        "message": "profile access granted",
        "username": payload.get("username"),
        "role": payload.get("role"),
        "scope": payload.get("scope"),
    }


@router.get("/admin")
def admin(payload=Depends(get_token_payload)):
    require_scope(payload.get("scope", ""), "admin:panel")
    require_role(payload.get("role", ""), "admin")
    return {
        "message": "admin access granted",
        "username": payload.get("username"),
        "role": payload.get("role"),
        "scope": payload.get("scope"),
    }

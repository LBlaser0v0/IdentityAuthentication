from fastapi import HTTPException


def require_scope(scope_string: str, required_scope: str):
    scopes = set(scope_string.split())
    if required_scope not in scopes:
        raise HTTPException(status_code=403, detail=f"missing scope: {required_scope}")


def require_role(role: str, required_role: str):
    if role != required_role:
        raise HTTPException(status_code=403, detail=f"missing role: {required_role}")

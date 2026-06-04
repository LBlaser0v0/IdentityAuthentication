import base64
import hashlib
import secrets
from dataclasses import dataclass


@dataclass(frozen=True)
class PkcePair:
    verifier: str
    challenge: str
    method: str


def build_pkce_pair(method: str = "S256", verifier_length_bytes: int = 48) -> PkcePair:
    verifier = secrets.token_urlsafe(verifier_length_bytes)
    if method == "S256":
        digest = hashlib.sha256(verifier.encode("utf-8")).digest()
        challenge = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
    elif method == "plain":
        challenge = verifier
    else:
        raise ValueError(f"unsupported PKCE method: {method}")
    return PkcePair(verifier=verifier, challenge=challenge, method=method)


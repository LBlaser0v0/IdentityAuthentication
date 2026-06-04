from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlencode, urlparse
import secrets

import httpx

from attack_simulator.config import DEFAULT_CONFIG, SimulatorConfig
from attack_simulator.pkce import PkcePair, build_pkce_pair


@dataclass(frozen=True)
class AuthorizationCapture:
    code: str
    request_state: str
    returned_state: str
    requested_scope: str
    location: str
    pkce: Optional[PkcePair] = None


class OAuthLabClient:
    """Small black-box client used by C-side attack experiments."""

    def __init__(self, config: SimulatorConfig = DEFAULT_CONFIG):
        self.config = config
        self.client = httpx.Client(timeout=config.timeout_seconds, follow_redirects=False)

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc, _tb):
        self.close()

    def check_services(self) -> Dict[str, Any]:
        targets = {
            "auth": self.config.auth_server_base,
            "client": self.config.client_app_base,
            "resource": self.config.resource_server_base,
        }
        status: Dict[str, Any] = {}
        for name, url in targets.items():
            try:
                status[name] = self.client.get(f"{url}/").status_code
            except Exception as exc:
                status[name] = f"unreachable: {exc}"
        return status

    def request_authorization_code(
        self,
        *,
        username: str,
        password: str,
        scope: str,
        state: Optional[str] = None,
        use_pkce: bool = False,
        pkce_method: str = "S256",
        verifier_length_bytes: int = 48,
    ) -> AuthorizationCapture:
        request_state = state or secrets.token_urlsafe(16)
        pkce = build_pkce_pair(pkce_method, verifier_length_bytes) if use_pkce else None

        authorize_params: Dict[str, Any] = {
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "scope": scope,
            "state": request_state,
        }
        if pkce:
            authorize_params["code_challenge"] = pkce.challenge
            authorize_params["code_challenge_method"] = pkce.method

        # Exercise GET /authorize first so the experiment follows the browser-visible flow.
        page_response = self.client.get(
            f"{self.config.auth_server_base}/authorize?{urlencode(authorize_params)}"
        )
        page_response.raise_for_status()

        form_data = {
            "username": username,
            "password": password,
            **authorize_params,
        }
        submit_response = self.client.post(
            f"{self.config.auth_server_base}/authorize",
            data=form_data,
        )
        if submit_response.status_code != 302:
            raise RuntimeError(
                f"authorization failed: status={submit_response.status_code}, body={submit_response.text}"
            )

        location = submit_response.headers["location"]
        query = parse_qs(urlparse(location).query)
        return AuthorizationCapture(
            code=query.get("code", [""])[0],
            request_state=request_state,
            returned_state=query.get("state", [""])[0],
            requested_scope=scope,
            location=location,
            pkce=pkce,
        )

    def exchange_code(
        self,
        code: str,
        *,
        code_verifier: str = "",
        client_secret: Optional[str] = None,
    ) -> httpx.Response:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret if client_secret is None else client_secret,
            "redirect_uri": self.config.redirect_uri,
        }
        if code_verifier:
            data["code_verifier"] = code_verifier
        return self.client.post(f"{self.config.auth_server_base}/token", data=data)

    def access_resource(self, access_token: str, path: str) -> httpx.Response:
        return self.client.get(
            f"{self.config.resource_server_base}{path}",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    def callback_with_state_cookie(
        self,
        *,
        code: str,
        query_state: str,
        cookie_state: Optional[str],
    ) -> httpx.Response:
        cookies = {}
        if cookie_state is not None:
            cookies["oauth_state"] = cookie_state
        return self.client.get(
            f"{self.config.client_app_base}/callback",
            params={"code": code, "state": query_state},
            cookies=cookies,
        )

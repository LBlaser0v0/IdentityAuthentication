from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import mean
from time import perf_counter
from typing import List, Optional, Tuple
import csv
import json

from attack_simulator.config import DEFAULT_CONFIG, SimulatorConfig
from attack_simulator.oauth_client import OAuthLabClient
from attack_simulator.pkce import build_pkce_pair


@dataclass
class ExperimentResult:
    experiment: str
    defense: str
    attack_success: bool
    token_status: Optional[int]
    resource_status: Optional[int]
    elapsed_ms: float
    reason: str
    evidence: dict = field(default_factory=dict)


def _elapsed_ms(started_at: float) -> float:
    return round((perf_counter() - started_at) * 1000, 2)


def _token_from_response(response) -> str:
    if response.status_code != 200:
        return ""
    return response.json().get("access_token", "")


def experiment_code_interception_without_pkce(client: OAuthLabClient) -> ExperimentResult:
    started_at = perf_counter()
    capture = client.request_authorization_code(
        username="alice",
        password="alice123",
        scope="read:profile read:email",
        state="c-lab-code-intercept-no-pkce",
        use_pkce=False,
    )
    token_response = client.exchange_code(capture.code)
    access_token = _token_from_response(token_response)
    profile_response = client.access_resource(access_token, "/profile") if access_token else None
    attack_success = token_response.status_code == 200 and profile_response is not None and profile_response.status_code == 200
    return ExperimentResult(
        experiment="authorization_code_interception",
        defense="no_pkce",
        attack_success=attack_success,
        token_status=token_response.status_code,
        resource_status=profile_response.status_code if profile_response else None,
        elapsed_ms=_elapsed_ms(started_at),
        reason="attacker can redeem an intercepted authorization code when no PKCE verifier is required"
        if attack_success
        else "intercepted code could not be redeemed",
        evidence={"returned_state": capture.returned_state, "granted_scope": token_response.json().get("scope") if token_response.status_code == 200 else ""},
    )


def experiment_code_interception_with_pkce(client: OAuthLabClient) -> ExperimentResult:
    started_at = perf_counter()
    capture = client.request_authorization_code(
        username="alice",
        password="alice123",
        scope="read:profile read:email",
        state="c-lab-code-intercept-pkce",
        use_pkce=True,
        pkce_method="S256",
    )
    attacker_token_response = client.exchange_code(capture.code)
    attack_success = attacker_token_response.status_code == 200
    legitimate_response = client.exchange_code(capture.code, code_verifier=capture.pkce.verifier if capture.pkce else "")
    return ExperimentResult(
        experiment="authorization_code_interception",
        defense="pkce_s256",
        attack_success=attack_success,
        token_status=attacker_token_response.status_code,
        resource_status=None,
        elapsed_ms=_elapsed_ms(started_at),
        reason="PKCE blocks the intercepted code because the attacker lacks the code_verifier"
        if not attack_success
        else "intercepted code was redeemed even though PKCE was enabled",
        evidence={
            "attacker_error": attacker_token_response.text,
            "legitimate_token_status_after_failed_attack": legitimate_response.status_code,
        },
    )


def experiment_login_csrf(client: OAuthLabClient) -> List[ExperimentResult]:
    results: List[ExperimentResult] = []
    capture = client.request_authorization_code(
        username="alice",
        password="alice123",
        scope="read:profile read:email",
        state="victim-original-state",
        use_pkce=False,
    )

    cases = [
        ("missing_saved_state", "victim-original-state", None, "client has no saved state cookie"),
        ("missing_query_state", "", "victim-original-state", "callback query has no state"),
        ("state_mismatch", "attacker-state", "victim-original-state", "callback state does not match saved state"),
    ]
    for defense, query_state, cookie_state, description in cases:
        started_at = perf_counter()
        response = client.callback_with_state_cookie(
            code=capture.code,
            query_state=query_state,
            cookie_state=cookie_state,
        )
        results.append(
            ExperimentResult(
                experiment="login_csrf",
                defense=defense,
                attack_success=response.status_code < 400,
                token_status=None,
                resource_status=response.status_code,
                elapsed_ms=_elapsed_ms(started_at),
                reason=f"blocked: {description}" if response.status_code >= 400 else f"not blocked: {description}",
                evidence={"callback_status": response.status_code, "callback_body": response.text[:300]},
            )
        )
    return results


def experiment_scope_abuse(client: OAuthLabClient) -> List[ExperimentResult]:
    results: List[ExperimentResult] = []

    scenarios = [
        ("alice", "alice123", "user_requests_admin_scope", False),
        ("admin", "admin123", "admin_requests_admin_scope", True),
    ]
    for username, password, defense, expected_admin_access in scenarios:
        started_at = perf_counter()
        capture = client.request_authorization_code(
            username=username,
            password=password,
            scope="read:profile read:email admin:panel",
            state=f"c-lab-scope-{username}",
            use_pkce=False,
        )
        token_response = client.exchange_code(capture.code)
        token = _token_from_response(token_response)
        admin_response = client.access_resource(token, "/admin") if token else None
        admin_access = admin_response is not None and admin_response.status_code == 200
        abuse_success = username == "alice" and admin_access
        results.append(
            ExperimentResult(
                experiment="scope_abuse",
                defense=defense,
                attack_success=abuse_success,
                token_status=token_response.status_code,
                resource_status=admin_response.status_code if admin_response else None,
                elapsed_ms=_elapsed_ms(started_at),
                reason="authorization server clips requested scope to user allowed scopes"
                if not abuse_success
                else "normal user gained admin resource access",
                evidence={
                    "username": username,
                    "expected_admin_access": expected_admin_access,
                    "granted_scope": token_response.json().get("scope") if token_response.status_code == 200 else "",
                },
            )
        )
    return results


def experiment_pkce_performance(iterations: int = 300) -> List[ExperimentResult]:
    results: List[ExperimentResult] = []
    for method in ["plain", "S256"]:
        for verifier_length_bytes in [32, 48, 64, 96]:
            timings = []
            for _ in range(iterations):
                started_at = perf_counter()
                build_pkce_pair(method=method, verifier_length_bytes=verifier_length_bytes)
                timings.append((perf_counter() - started_at) * 1000)
            timings_sorted = sorted(timings)
            p95_index = int(len(timings_sorted) * 0.95) - 1
            results.append(
                ExperimentResult(
                    experiment="pkce_performance",
                    defense=f"{method}_{verifier_length_bytes}_bytes",
                    attack_success=False,
                    token_status=None,
                    resource_status=None,
                    elapsed_ms=round(sum(timings), 2),
                    reason="local PKCE verifier/challenge generation timing",
                    evidence={
                        "iterations": iterations,
                        "method": method,
                        "verifier_length_bytes": verifier_length_bytes,
                        "avg_ms": round(mean(timings), 6),
                        "p95_ms": round(timings_sorted[p95_index], 6),
                        "max_ms": round(max(timings), 6),
                    },
                )
            )
    return results


def run_all_experiments(config: SimulatorConfig = DEFAULT_CONFIG, pkce_iterations: int = 300) -> List[ExperimentResult]:
    with OAuthLabClient(config) as client:
        service_status = client.check_services()
        if any(status != 200 for status in service_status.values()):
            raise RuntimeError(f"services are not ready: {service_status}")

        results: List[ExperimentResult] = [
            experiment_code_interception_without_pkce(client),
            experiment_code_interception_with_pkce(client),
        ]
        results.extend(experiment_login_csrf(client))
        results.extend(experiment_scope_abuse(client))
        results.extend(experiment_pkce_performance(iterations=pkce_iterations))
        return results


def write_results(results: List[ExperimentResult], results_dir: Path = DEFAULT_CONFIG.results_dir) -> Tuple[Path, Path]:
    results_dir.mkdir(parents=True, exist_ok=True)
    rows = [asdict(result) for result in results]

    json_path = results_dir / "latest_results.json"
    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    csv_path = results_dir / "latest_summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "experiment",
                "defense",
                "attack_success",
                "token_status",
                "resource_status",
                "elapsed_ms",
                "reason",
                "evidence",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    return json_path, csv_path

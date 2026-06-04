from pathlib import Path
import argparse
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from attack_simulator.experiments import run_all_experiments, write_results


def main() -> int:
    parser = argparse.ArgumentParser(description="Run C-side OAuth attack and PKCE experiments.")
    parser.add_argument(
        "--pkce-iterations",
        type=int,
        default=300,
        help="Iterations per PKCE timing case.",
    )
    args = parser.parse_args()

    results = run_all_experiments(pkce_iterations=args.pkce_iterations)
    json_path, csv_path = write_results(results)

    print("[C EXPERIMENTS]")
    for result in results:
        print(
            f"{result.experiment:32} {result.defense:28} "
            f"attack_success={str(result.attack_success):5} "
            f"token={result.token_status} resource={result.resource_status} "
            f"elapsed_ms={result.elapsed_ms}"
        )
    print()
    print(f"json={json_path}")
    print(f"csv={csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


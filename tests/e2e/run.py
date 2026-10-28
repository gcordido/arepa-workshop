"""Run deterministic lifecycle checks exclusively against disposable local services."""

import argparse
import json
import os
from pathlib import Path
import sys
import unittest
from dotenv import dotenv_values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite", choices=("contract", "agent", "all"), default="contract")
    parser.add_argument("--env-file", type=Path, default=Path(__file__).resolve().parents[2] / ".env")
    parser.add_argument("--server-repo", required=True, type=Path)
    parser.add_argument("--server-python", required=True, type=Path)
    parser.add_argument("--azurite", type=Path)
    parser.add_argument("--artifacts", required=True, type=Path)
    args = parser.parse_args()
    os.environ.update({
        "AREPA_SERVER_REPO": str(args.server_repo.resolve()),
        "AREPA_SERVER_PYTHON": str(args.server_python.absolute()),
        "AREPA_E2E_ARTIFACTS": str(args.artifacts.resolve()),
    })
    if args.azurite:
        os.environ["AREPA_AZURITE"] = str(args.azurite.absolute())
    if args.suite in ("agent", "all"):
        values = dotenv_values(args.env_file)
        for key in ("FOUNDRY_ENDPOINT", "FOUNDRY_API_KEY", "FOUNDRY_MODEL_DEPLOYMENT"):
            value = os.environ.get(key) or values.get(key) or ""
            if not value.strip() or "<" in value or ">" in value:
                parser.error(f"Set {key} for model-backed tests through --env-file or environment.")
            os.environ[key] = value
    suite = unittest.TestSuite()
    names = ("contract", "agent") if args.suite == "all" else (args.suite,)
    for name in names:
        suite.addTests(unittest.defaultTestLoader.discover(str(Path(__file__).parent),
                                                          pattern=f"test_{name}.py"))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    summary = {
        "tests_run": result.testsRun,
        "failures": len(result.failures), "errors": len(result.errors),
        "skipped": len(result.skipped),
        "suite": args.suite,
        "model_deployment": os.environ.get("FOUNDRY_MODEL_DEPLOYMENT") if args.suite != "contract" else None,
        "passed": result.wasSuccessful() and result.testsRun > 0 and not result.skipped,
    }
    args.artifacts.mkdir(parents=True, exist_ok=True)
    (args.artifacts / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())

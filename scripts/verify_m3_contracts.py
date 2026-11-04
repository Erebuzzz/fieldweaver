"""Check release-facing frontend artifacts and the public evaluation snapshot."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_SRC = ROOT / "frontend" / "src"
PUBLIC_DIR = ROOT / "frontend" / "public"


def test_frontend_style_rule() -> bool:
    print("--- 1. FRONTEND PUNCTUATION RULE ---")
    violations = []
    for suffix in ("*.ts", "*.tsx", "*.css"):
        for path in FRONTEND_SRC.rglob(suffix):
            content = path.read_text(encoding="utf-8")
            if chr(0x2014) in content or "&mdash;" in content:
                violations.append(str(path.relative_to(ROOT)))

    if violations:
        print(f"FAIL: Emdash found in {violations}")
        return False

    print("PASS: No emdash found in frontend source.")
    return True


def test_client_secret_isolation() -> bool:
    print("--- 2. CLIENT SECRET ISOLATION ---")
    violations = []
    key_pattern = re.compile(r"[\"'](?:bt-|b10-)[a-zA-Z0-9_-]{24,}[\"']")

    for suffix in ("*.ts", "*.tsx"):
        for path in FRONTEND_SRC.rglob(suffix):
            content = path.read_text(encoding="utf-8")
            if "NEXT_PUBLIC_BASETEN_API_KEY" in content or key_pattern.search(content):
                violations.append(str(path.relative_to(ROOT)))

    if violations:
        print(f"FAIL: Potential provider credential reference in {violations}")
        return False

    print("PASS: No provider key is referenced in client source.")
    return True


def test_documentation_route_artifacts() -> bool:
    print("--- 3. DOCUMENTATION ROUTE ARTIFACTS ---")
    required = [
        FRONTEND_SRC / "app" / "docs" / "page.tsx",
        FRONTEND_SRC / "components" / "docs" / "subsystem-explorer.tsx",
        FRONTEND_SRC / "components" / "docs" / "lifecycle-visualizer.tsx",
        FRONTEND_SRC / "components" / "docs" / "api-console.tsx",
        FRONTEND_SRC / "components" / "docs" / "safety-browser.tsx",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    empty = [
        str(path.relative_to(ROOT))
        for path in required
        if path.is_file() and not path.read_text(encoding="utf-8").strip()
    ]

    if missing or empty:
        print(f"FAIL: Missing files {missing}; empty files {empty}")
        return False

    print("PASS: Documentation route and referenced modules exist.")
    return True


def _find_private_fields(value: Any, path: str = "report") -> list[str]:
    forbidden = {
        "ground_truth",
        "source",
        "source_x",
        "source_y",
        "truth_field",
        "kappa",
    }
    found = []

    if isinstance(value, dict):
        for key, item in value.items():
            if key.lower() in forbidden:
                found.append(f"{path}.{key}")
            found.extend(_find_private_fields(item, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(_find_private_fields(item, f"{path}[{index}]"))

    return found


def test_evaluation_report_integrity() -> bool:
    print("--- 4. PUBLIC EVALUATION REPORT ---")
    report_path = PUBLIC_DIR / "evaluation-report.json"
    if not report_path.is_file():
        print("FAIL: public/evaluation-report.json is missing.")
        return False

    data = json.loads(report_path.read_text(encoding="utf-8"))
    required = {"configuration", "controller_summary", "runs"}
    if not required.issubset(data):
        print(f"FAIL: Required top-level fields missing: {sorted(required - data.keys())}")
        return False

    runs = data["runs"]
    scenario_ids = {run["scenario_id"] for run in runs}
    configured_scenarios = data["configuration"]["scenario_count"]
    private_fields = _find_private_fields(data)

    if not runs or len(scenario_ids) != configured_scenarios:
        print("FAIL: Run records do not match the configured scenario count.")
        return False
    if private_fields:
        print(f"FAIL: Private fields present in public report: {private_fields}")
        return False

    print(
        f"PASS: {len(runs)} run records cover {len(scenario_ids)} scenarios "
        "without hidden-source fields."
    )
    return True


def main() -> None:
    print("=== FIELDWEAVER RELEASE ARTIFACT CHECKS ===")
    results = [
        test_frontend_style_rule(),
        test_client_secret_isolation(),
        test_documentation_route_artifacts(),
        test_evaluation_report_integrity(),
    ]
    if all(results):
        print("=== ALL RELEASE ARTIFACT CHECKS PASSED ===")
        return

    print("=== RELEASE ARTIFACT CHECKS FAILED ===")
    sys.exit(1)


if __name__ == "__main__":
    main()

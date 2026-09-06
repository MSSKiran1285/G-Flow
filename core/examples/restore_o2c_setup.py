"""Reimports the O2C Object Library (VA01/VL01N/VL02N/VF01 Modules) and Scripts
(TestCases) captured in the script-builder UI, from o2c_object_library_export.json.

The local repository.db is gitignored (core/data/ — see .gitignore's own comment on
why: mined master data can carry real business data), so a fresh machine's DB starts
empty on first run. This restores just the *structural* work — captured component
ids, semantic names, script steps/bindings — none of which is sensitive; no live SAP
data is included. Run once after cloning + starting the FastAPI backend, from the
repo root:

    core/.venv/Scripts/python core/examples/restore_o2c_setup.py

Safe to re-run: both POST /api/modules and POST /api/test-cases replace an
existing entry with the same name (see save_module/define_test_case_from_spec).
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

API_BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000/api"
EXPORT_PATH = Path(__file__).parent / "o2c_object_library_export.json"


def post(path: str, body: dict) -> dict:
    req = urllib.request.Request(
        f"{API_BASE}{path}", data=json.dumps(body).encode(), method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def main() -> None:
    data = json.loads(EXPORT_PATH.read_text(encoding="utf-8"))

    for module in data["modules"]:
        result = post("/modules", module)
        print(f"  Module {result['module_name']!r}: {result['attribute_count']} attributes")

    for test_case in data["test_cases"]:
        result = post("/test-cases", test_case)
        print(f"  Script {result['name']!r} defined")

    print(f"\nRestored {len(data['modules'])} modules and {len(data['test_cases'])} scripts against {API_BASE}")


if __name__ == "__main__":
    main()

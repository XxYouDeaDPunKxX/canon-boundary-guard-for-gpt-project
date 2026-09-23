"""Run local checks and write results for the exact plugin bytes tested.

python -B -X utf8 tools/verify_plugin.py
Install requirements-test.txt in the test environment to exercise the optional
legacy schema branch. Missing dependencies are reported as skips, not passes.
This runner does not test the ChatGPT host or change plugin instructions.
"""
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import io
import json
from pathlib import Path
import platform
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
PLUGIN = ROOT / "plugin/canon-boundary-guard"
SKILL = PLUGIN / "skills/canon-boundary-guard/SKILL.md"


class RecordedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.passed_ids = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.passed_ids.append(test.id())


def main():
    sys.dont_write_bytecode = True
    DIST.mkdir(exist_ok=True)
    manifest = json.loads((PLUGIN / "plugin.json").read_text(encoding="utf-8"))
    log = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"))
    result = unittest.TextTestRunner(stream=log, verbosity=2, resultclass=RecordedResult).run(suite)
    log_path = DIST / f"UNIT_TESTS_{manifest['version']}.txt"
    log_path.write_text(log.getvalue(), encoding="utf-8")

    runs = []
    for arguments in (["tools/package_plugin.py"],
                      ["tools/audit_plugin_scripts.py", "--output", "dist/SCRIPT_CODE_AUDIT.json"]):
        process = subprocess.run([sys.executable, "-B", "-X", "utf8", *arguments],
                                 cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
        runs.append({"command": [sys.executable, "-B", "-X", "utf8", *arguments],
                     "exit_code": process.returncode, "stdout": process.stdout, "stderr": process.stderr})
    try:
        dependency_version = importlib.metadata.version("jsonschema")
    except importlib.metadata.PackageNotFoundError:
        dependency_version = None
    archive = DIST / f"{manifest['name']}-{manifest['version']}.zip"
    built = runs[0]["exit_code"] == 0
    audit = json.loads(runs[1]["stdout"]) if runs[1]["exit_code"] == 0 else None
    host_report = DIST / f"CHATGPT_WEB_TEST_{manifest['version']}.md"
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target": "ChatGPT web", "version": manifest["version"],
        "scope": "Local repository, archive and helper checks; not ChatGPT host execution or agent behavior.",
        "environment": {"system": platform.system(), "python": platform.python_version(),
                        "jsonschema": dependency_version},
        "skill_sha256": hashlib.sha256(SKILL.read_bytes()).hexdigest(),
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest() if built else None,
        "tests": {"run": result.testsRun, "passed": len(result.passed_ids),
                  "failed": len(result.failures), "errors": len(result.errors),
                  "skipped": [{"test": test.id(), "reason": reason} for test, reason in result.skipped],
                  "expected_failures": [test.id() for test, _ in result.expectedFailures],
                  "unexpected_successes": [test.id() for test in result.unexpectedSuccesses],
                  "passed_ids": result.passed_ids, "log": log_path.name},
        "helper_audit": {"run": len(audit["checks"]), "failed": audit["failed"]} if audit else None,
        "commands": runs,
        "activation": "User accepts custom instructions or explicit plugin tag; automatic startup is not an acceptance requirement.",
        "chatgpt_host_evidence": {"report": host_report.name if host_report.is_file() else None,
                                 "scope": "Recorded separately; never inferred from this local run."},
    }
    (DIST / "CHATGPT_TECHNICAL_CHECK.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"version": report["version"], "tests_run": result.testsRun,
                      "passed": len(result.passed_ids), "skipped": len(result.skipped),
                      "failures": len(result.failures), "errors": len(result.errors),
                      "helper_audit": report["helper_audit"],
                      "command_exit_codes": [run["exit_code"] for run in runs]}, indent=2))
    return 0 if result.wasSuccessful() and all(run["exit_code"] == 0 for run in runs) else 1


if __name__ == "__main__":
    raise SystemExit(main())

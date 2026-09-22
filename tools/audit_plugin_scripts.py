"""Reproduce script behavior without changing the protocol or plugin.

Example:
  python tools/audit_plugin_scripts.py --jsonschema-path PATH --output dist/SCRIPT_CODE_AUDIT.json
The optional path contains an isolated installation of jsonschema.
Exit 1 means a required behavior tested here failed; observations are separate.
"""

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "plugin/canon-boundary-guard/skills/canon-boundary-guard-gpt-project"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--jsonschema-path", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.jsonschema_path:
        sys.path.insert(0, str(args.jsonschema_path.resolve()))
    sys.dont_write_bytecode = True
    validation = load("cbg_validation", SKILL / "scripts/validate_state.py")
    proof = load("cbg_proof", SKILL / "scripts/extract_proof.py")
    fingerprint = load("cbg_fingerprint", SKILL / "scripts/artifact_fingerprint.py")
    state = {"protocol": "canon-boundary-guard:gpt-project-adapter", "protocol_version": "1.1",
             "state_seq": 1, "updated_at": "2026-09-22T00:00:00Z",
             "active_l0_sources": [{"source_id": "synthetic-fixture", "source_type": "local_file", "status": "inspected"}],
             "authorized_deltas": [], "open_conflicts": [], "pending_decisions": [], "last_persistent_artifacts": []}
    delta = {"type": "CANON_STATE_DELTA", "seq": 1, "timestamp": "2026-09-22T00:00:00Z",
             "basis": {"previous_seq": 0},
             "decision": {"mode": "B", "summary": "Synthetic audit only", "authorized_delta": "", "affected_targets": []},
             "current_state": state, "operator_action_required": "Synthetic audit only"}
    checks, observations = [], []

    def check(name, actual, expected):
        checks.append({"case": name, "passed": actual == expected, "expected": expected, "actual": actual})

    validator_backend = validation.validate_with_jsonschema
    backends = [("fallback", lambda *unused: None)]
    if validator_backend(state, json.loads(validation.STATE_SCHEMA_PATH.read_text()), "state") is not None:
        backends.append(("jsonschema", validator_backend))
    for backend_name, backend in backends:
        validation.validate_with_jsonschema = backend
        check(f"{backend_name}: valid state", not validation.validate_state_obj(state), True)
        check(f"{backend_name}: valid full delta", not validation.validate_delta_obj(delta), True)
        check(f"{backend_name}: boolean sequence rejected", not validation.validate_state_obj(dict(state, state_seq=True)), False)
        check(f"{backend_name}: additional property rejected", not validation.validate_state_obj(dict(state, unexpected=1)), False)
        check(f"{backend_name}: wrong protocol rejected", not validation.validate_state_obj(dict(state, protocol="other")), False)
        check(f"{backend_name}: integral JSON number accepted", not validation.validate_state_obj(dict(state, state_seq=1.0)), True)
        mismatch = dict(delta, current_state=dict(state, state_seq=2))
        check(f"{backend_name}: integer delta mismatch rejected", not validation.validate_delta_obj(mismatch), False)
        check(f"{backend_name}: integral-float delta mismatch rejected", not validation.validate_delta_obj(dict(mismatch, seq=1.0)), False)
        observations.append({"case": f"{backend_name}: schema-only state check",
                             "input": "empty active_l0_sources and updated_at='not-a-date'",
                             "errors": validation.validate_state_obj(dict(state, active_l0_sources=[], updated_at="not-a-date"))})

    ten_words = "one two three four five six seven eight nine ten"
    check("proof: exactly ten words use two groups of five", proof.first_last_five(ten_words),
          (ten_words.split()[:5], ten_words.split()[-5:]))
    short_words = "one two three"
    check("proof: fewer than ten words returns complete section", proof.first_last_five(short_words),
          (short_words.split(), short_words.split()))
    markdown = "## Target\nalpha beta gamma delta epsilon zeta eta theta iota kappa\n## Next\nomega\n"
    selected = proof.select_markdown_section(markdown.splitlines(keepends=True), "## Target")
    check("proof: ordinary ATX section boundaries", list(selected[:3]), ["## Target", 1, 2])
    for fence in ("```", "~~~"):
        markdown = f"## Target\none two three four five\n{fence}text\n## Example inside code\nsix seven\n{fence}\neight nine ten eleven twelve\n## Next\nend\n"
        selected = proof.select_markdown_section(markdown.splitlines(keepends=True), "## Target")
        check(f"proof: {fence} fenced heading stays in section", list(selected[:3]), ["## Target", 1, 7])
    markdown = "Introduction\nTarget\nThis is body text.\n## Target\nActual section body.\n## Next\nend\n"
    selected = proof.select_markdown_section(markdown.splitlines(keepends=True), "Target")
    check("proof: heading-text selector ignores plain body line", list(selected[:3]), ["## Target", 4, 5])

    with tempfile.TemporaryDirectory(prefix="cbg-script-cases-") as directory:
        task_tmp = Path(directory)
        artifact = task_tmp / "artifact.bin"
        artifact.write_bytes(b"abc\x00\xff")
        result = fingerprint.fingerprint(artifact)
        check("fingerprint: SHA256 and size", [result["size_bytes"], result["sha256"]],
              [5, hashlib.sha256(artifact.read_bytes()).hexdigest()])
        missing = task_tmp / "missing.bin"
        check("fingerprint: missing file reported", fingerprint.fingerprint(missing)["exists"], False)
        process = subprocess.run([sys.executable, str(SKILL / "scripts/artifact_fingerprint.py"), str(missing)],
                                 capture_output=True, text=True, encoding="utf-8", cwd=task_tmp)
        observations.append({"case": "fingerprint CLI missing file", "exit_code": process.returncode,
                             "result": json.loads(process.stdout)})
        duplicate = task_tmp / "duplicate-state.json"
        duplicate.write_text(json.dumps(state).replace('"state_seq": 1', '"state_seq": 0, "state_seq": 1'), encoding="utf-8")
        parsed = validation.load_json(duplicate)
        observations.append({"case": "duplicate JSON property", "raw_values": [0, 1],
                             "parsed_value": parsed["state_seq"], "errors": validation.validate_state_obj(parsed)})

    original = ROOT / "canon-boundary-guard-gpt"
    copies = list((original / "scripts").glob("*.py")) + list((original / "schemas").glob("*.json"))
    check("conversion: script and schema bytes unchanged",
          all(p.read_bytes() == (SKILL / p.relative_to(original)).read_bytes() for p in copies), True)
    embedded = json.loads((SKILL / "schemas/CANON_STATE_DELTA.schema.json").read_text())["properties"]["current_state"]
    check("schemas: embedded state schema matches standalone", embedded,
          json.loads((SKILL / "schemas/SESSION_STATE.schema.json").read_text()))
    # Avoid storing the full schemas in the otherwise compact report.
    checks[-1].update(expected="identical", actual="identical" if checks[-1]["passed"] else "different")
    report = {"python": sys.version.split()[0], "skill_directory": str(SKILL),
              "backends_exercised": [name for name, _ in backends], "checks": checks,
              "failed": sum(not item["passed"] for item in checks), "observations": observations,
              "audit_modifies_bundle": False,
              "plugin_version": json.loads((ROOT / "plugin/canon-boundary-guard/plugin.json").read_text(encoding="utf-8"))["version"]}
    serialized = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(serialized + "\n", encoding="utf-8")
    print(serialized)
    return 1 if report["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

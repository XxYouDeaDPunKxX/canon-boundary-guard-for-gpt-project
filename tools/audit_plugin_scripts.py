"""Audit the two mechanical helpers shipped in the ChatGPT plugin.

Run: python tools/audit_plugin_scripts.py --output dist/SCRIPT_CODE_AUDIT.json
The original source bundle's state validator is covered by tests/test_helpers.py.
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
SKILL = ROOT / "plugin/canon-boundary-guard/skills/canon-boundary-guard"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SKILL / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    sys.dont_write_bytecode = True
    proof = load("extract_proof")
    fingerprint = load("artifact_fingerprint")
    checks, observations = [], []

    def check(name, actual, expected):
        checks.append({"case": name, "passed": actual == expected,
                       "expected": expected, "actual": actual})

    words = "one two three four five six seven eight nine ten".split()
    check("ten-word proof uses two groups of five", proof.first_last_five(" ".join(words)),
          (words[:5], words[-5:]))
    check("short proof uses entire section", proof.first_last_five("one two three"),
          (["one", "two", "three"], ["one", "two", "three"]))
    cases = [
        ("ordinary heading", "## Target\nbody\n## Next\nother\n", "Target", ("## Target", 1, 2)),
        ("indented closed heading", "   ## Target ###\nbody\n  ## Next\nother\n", "Target", ("   ## Target ###", 1, 2)),
        ("empty sibling", "## Target\nbody\n##\nother\n", "Target", ("## Target", 1, 2)),
        ("plain line cannot shadow heading", "Target\ntext\n## Target\nbody\n## Next\n", "Target", ("## Target", 3, 4)),
        ("nested headings", "## Target\nbody\n### Child\nchild\n## Next\n", "Target", ("## Target", 1, 4)),
        ("CRLF heading", "## Target\r\nbody\r\n## Next\r\n", "Target", ("## Target", 1, 2)),
        ("literal hash", "## C#\nbody\n## Next\n", "C#", ("## C#", 1, 2)),
    ]
    for name, text, selector, expected in cases:
        check(name, proof.select_markdown_section(text.splitlines(keepends=True), selector)[:3], expected)
    for fence in ("~~~", "```"):
        text = f"## Target\none\n{fence}\n## Example\ntwo\n{fence}\nthree\n## Next\n"
        check("fenced heading " + fence,
              proof.select_markdown_section(text.splitlines(keepends=True), "Target")[:3],
              ("## Target", 1, 7))

    with tempfile.TemporaryDirectory(prefix="cbg-plugin-audit-") as directory:
        task_tmp = Path(directory)
        source = task_tmp / "source.md"
        source.write_text("## Target\none two three four five six seven eight nine ten\n## Next\n",
                          encoding="utf-8-sig")
        process = subprocess.run([sys.executable, "-B", str(SKILL / "scripts/extract_proof.py"),
                                  str(source), "--heading", "Target", "--json"],
                                 cwd=task_tmp, capture_output=True, text=True, encoding="utf-8")
        check("proof CLI accepts BOM and unrelated cwd", process.returncode, 0)
        if process.returncode == 0:
            check("proof CLI span", json.loads(process.stdout)["line_range"], [1, 2])
        binary = task_tmp / "artifact.bin"
        binary.write_bytes(bytes([97, 98, 99, 0, 255]))
        result = fingerprint.fingerprint(binary)
        check("binary fingerprint hash", result["sha256"], hashlib.sha256(binary.read_bytes()).hexdigest())
        check("binary fingerprint size", result["size_bytes"], 5)
        missing = task_tmp / "missing.bin"
        process = subprocess.run([sys.executable, "-B", str(SKILL / "scripts/artifact_fingerprint.py"),
                                  str(missing)], cwd=task_tmp, capture_output=True, text=True, encoding="utf-8")
        check("missing fingerprint is explicit", json.loads(process.stdout)[0]["exists"], False)
        observations.append({"case": "missing fingerprint CLI", "exit_code": process.returncode,
                             "meaning": "Inspect exists; a zero exit code does not establish file existence."})

    for name in ("extract_proof.py", "artifact_fingerprint.py"):
        check("source copy: " + name, (SKILL / "scripts" / name).read_bytes() ==
              (ROOT / "canon-boundary-guard-gpt/scripts" / name).read_bytes(), True)
    check("native script inventory", sorted(p.name for p in (SKILL / "scripts").glob("*.py")),
          ["artifact_fingerprint.py", "extract_proof.py"])

    report = {"python": sys.version.split()[0], "skill_directory": str(SKILL),
              "scope": "Native ChatGPT plugin helpers only; no state validator is shipped.",
              "checks": checks, "failed": sum(not item["passed"] for item in checks),
              "observations": observations, "audit_modifies_bundle": False,
              "plugin_version": json.loads((ROOT / "plugin/canon-boundary-guard/plugin.json").read_text())["version"]}
    serialized = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(serialized + "\n", encoding="utf-8")
    print(serialized)
    return 1 if report["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

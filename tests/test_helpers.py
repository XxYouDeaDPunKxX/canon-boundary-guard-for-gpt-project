"""Behavioral regressions for the source bundle and its native plugin copy.

Run: python -B -m unittest discover -s tests -v
Set CBG_TEST_BUNDLE to test an extracted/installed skill instead of the source.
"""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
BUNDLE = Path(os.environ.get("CBG_TEST_BUNDLE", ROOT / "canon-boundary-guard-gpt")).resolve()
sys.dont_write_bytecode = True


def load(name):
    spec = importlib.util.spec_from_file_location(name, BUNDLE / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validation = load("validate_state")
proof = load("extract_proof")
fingerprint = load("artifact_fingerprint")
HAS_JSONSCHEMA = importlib.util.find_spec("jsonschema") is not None


def state(seq=1):
    return {"protocol": "canon-boundary-guard:gpt-project-adapter", "protocol_version": "1.1",
            "state_seq": seq, "updated_at": "2026-09-22T00:00:00Z",
            "active_l0_sources": [{"source_id": "synthetic", "source_type": "local_file", "status": "inspected"}],
            "authorized_deltas": [], "open_conflicts": [], "pending_decisions": [], "last_persistent_artifacts": []}


def delta(seq=1, state_seq=1):
    return {"type": "CANON_STATE_DELTA", "seq": seq, "timestamp": "2026-09-22T00:00:00Z",
            "basis": {"previous_seq": 0},
            "decision": {"mode": "B", "summary": "Synthetic regression fixture", "authorized_delta": "", "affected_targets": []},
            "current_state": state(state_seq), "operator_action_required": "Synthetic fixture only"}


class ValidationCases:
    def test_integral_numbers_are_valid_sequence_values(self):
        for value in (0, 0.0, 1, 1.0, 1e0, 10**30):
            with self.subTest(value=value):
                self.assertEqual(validation.validate_state_obj(state(value)), [])

    def test_non_integer_and_negative_sequences_are_rejected(self):
        for value in (True, False, -1, -1.0, 1.5, "1", None, float("inf"), float("nan")):
            with self.subTest(value=value):
                self.assertTrue(validation.validate_state_obj(state(value)))

    def test_equal_integral_delta_sequences_are_accepted(self):
        for seq, state_seq in ((1, 1), (1.0, 1), (1, 1.0), (1.0, 1.0)):
            with self.subTest(seq=seq, state_seq=state_seq):
                self.assertEqual(validation.validate_delta_obj(delta(seq, state_seq)), [])

    def test_delta_sequence_mismatch_is_always_rejected(self):
        for seq, state_seq in ((1, 2), (1.0, 2), (1, 2.0), (1.0, 2.0)):
            with self.subTest(seq=seq, state_seq=state_seq):
                self.assertTrue(validation.validate_delta_obj(delta(seq, state_seq)))

    def test_existing_structural_constraints_are_enforced(self):
        for key in state():
            malformed = state()
            del malformed[key]
            with self.subTest(missing=key):
                self.assertTrue(validation.validate_state_obj(malformed))
        for changes in ({"protocol": "other"}, {"protocol_version": "2"}, {"extra": 1},
                        {"active_l0_sources": [{"source_id": "x", "source_type": "unknown", "status": "inspected"}]}):
            with self.subTest(changes=changes):
                malformed = dict(state(), **changes)
                self.assertTrue(validation.validate_state_obj(malformed))


class FallbackValidation(ValidationCases, unittest.TestCase):
    def setUp(self):
        # Select the real fallback even when jsonschema is installed.
        dependency = patch.object(validation, "validate_with_jsonschema", return_value=None)
        dependency.start()
        self.addCleanup(dependency.stop)


@unittest.skipUnless(HAS_JSONSCHEMA, "optional jsonschema is not installed")
class JsonschemaValidation(ValidationCases, unittest.TestCase):
    pass


class ProofExtraction(unittest.TestCase):
    def select(self, text, heading="## Target"):
        return proof.select_markdown_section(text.splitlines(keepends=True), heading)

    def test_exactly_ten_words_returns_five_at_each_end(self):
        self.assertEqual(proof.first_last_five("one two three four five six seven eight nine ten"),
                         (["one", "two", "three", "four", "five"], ["six", "seven", "eight", "nine", "ten"]))

    def test_short_section_is_returned_in_full(self):
        self.assertEqual(proof.first_last_five("one two three"), (["one", "two", "three"], ["one", "two", "three"]))

    def test_nested_headings_belong_to_parent_section(self):
        text = "## Target\nbody\n### Child\nchild body\n## Next\nend\n"
        self.assertEqual(self.select(text)[:3], ("## Target", 1, 4))

    def test_fenced_headings_do_not_end_sections(self):
        for opener, closer in (("```python", "```"), ("~~~text", "~~~"), ("````", "`````"), ("   ```", "  ```")):
            with self.subTest(opener=opener):
                text = f"## Target\none\n{opener}\n## Example\ntwo\n{closer}\nthree\n## Next\nend\n"
                selected = self.select(text)
                self.assertEqual(selected[:3], ("## Target", 1, 7))
                self.assertEqual(selected[3], "".join(text.splitlines(keepends=True)[:7]))

    def test_fenced_heading_cannot_be_selected(self):
        for fence in ("```", "~~~"):
            with self.subTest(fence=fence):
                text = f"{fence}\n## Target\nexample\n{fence}\n## Target\nactual\n## Next\n"
                for selector in ("## Target", "Target"):
                    self.assertEqual(self.select(text, selector)[:3], ("## Target", 5, 6))

    def test_only_fenced_heading_is_reported_missing(self):
        with self.assertRaises(ValueError):
            self.select("```\n## Target\n```\n")

    def test_fence_requires_matching_character_length_and_empty_tail(self):
        text = "## Target\n````python\n```\n## Example1\n~~~~\n## Example2\n```` trailing\n## Example3\n````\nlast\n## Next\n"
        self.assertEqual(self.select(text)[:3], ("## Target", 1, 10))

    def test_unclosed_fence_continues_to_end_of_file(self):
        text = "## Target\n```\n## Example\nbody\n"
        self.assertEqual(self.select(text)[:3], ("## Target", 1, 4))

    def test_plain_line_cannot_shadow_heading_text(self):
        text = "Introduction\nTarget\nordinary body\n## Target\nactual\n## Next\nend\n"
        self.assertEqual(self.select(text, "Target")[:3], ("## Target", 4, 5))

    def test_missing_heading_is_an_error(self):
        with self.assertRaises(ValueError):
            self.select("## Other\nbody\n")


class CliAndFiles(unittest.TestCase):
    def run_script(self, name, directory, *arguments):
        return subprocess.run([sys.executable, "-B", "-X", "utf8", str(BUNDLE / "scripts" / name), *map(str, arguments)],
                              cwd=directory, capture_output=True, text=True, encoding="utf-8")

    def test_schema_paths_and_bom_work_from_unrelated_directory(self):
        with tempfile.TemporaryDirectory(prefix="cbg-regression-") as directory:
            path = Path(directory) / "state.json"
            path.write_text(json.dumps(state()), encoding="utf-8-sig")
            result = self.run_script("validate_state.py", directory, "--state", path, "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(json.loads(result.stdout)["valid"])

    @unittest.skipUnless(HAS_JSONSCHEMA, "optional jsonschema is not installed")
    def test_cli_rejects_integral_float_delta_mismatch(self):
        with tempfile.TemporaryDirectory(prefix="cbg-regression-") as directory:
            path = Path(directory) / "delta.json"
            path.write_text(json.dumps(delta(1.0, 2)), encoding="utf-8")
            result = self.run_script("validate_state.py", directory, "--delta", path, "--json")
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertFalse(json.loads(result.stdout)["valid"])

    def test_proof_cli_reports_the_actual_heading_and_boundaries(self):
        with tempfile.TemporaryDirectory(prefix="cbg-regression-") as directory:
            path = Path(directory) / "source.md"
            path.write_text("Target\n## Target\none two three four five six seven eight nine ten\n## Next\nend\n", encoding="utf-8-sig")
            result = self.run_script("extract_proof.py", directory, path, "--heading", "Target", "--json")
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["heading"], "## Target")
            self.assertEqual(report["line_range"], [2, 3])
            self.assertEqual(report["last_5_words"], ["six", "seven", "eight", "nine", "ten"])

    def test_fingerprint_hashes_binary_bytes_and_reports_missing_file(self):
        with tempfile.TemporaryDirectory(prefix="cbg-regression-") as directory:
            path = Path(directory) / "artifact.bin"
            path.write_bytes(b"abc\x00\xff")
            result = fingerprint.fingerprint(path)
            self.assertEqual(result["size_bytes"], 5)
            self.assertEqual(result["sha256"], "77cb6bea091ff250af304a09024b0c526be6a21014a91ab56e788c63a69e811f")
            self.assertFalse(fingerprint.fingerprint(Path(directory) / "missing")["exists"])


if __name__ == "__main__":
    unittest.main()

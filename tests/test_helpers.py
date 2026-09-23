"""Behavioral regressions for the original source bundle and its shared helpers.

Run: python -B -m unittest discover -s tests -v
Set CBG_TEST_BUNDLE to test an extracted original source bundle.
The smaller native plugin is exercised by test_plugin_package.py.
"""

import importlib.util
from decimal import Decimal
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

    def test_json_loader_preserves_fractional_sequence_values(self):
        with tempfile.TemporaryDirectory(prefix="cbg-exact-json-") as directory:
            path = Path(directory) / "state.json"
            for token in ("1.0000000000000001", "0.99999999999999999", "1e-1000"):
                with self.subTest(token=token):
                    path.write_text(json.dumps(state()).replace('"state_seq": 1', '"state_seq": ' + token), encoding="utf-8")
                    self.assertTrue(validation.validate_state_obj(validation.load_json(path)))

    def test_json_loader_keeps_large_exponents_compact(self):
        with tempfile.TemporaryDirectory(prefix="cbg-exact-json-") as directory:
            path = Path(directory) / "state.json"
            path.write_text(json.dumps(state()).replace('"state_seq": 1', '"state_seq": 1e1000000'), encoding="utf-8")
            loaded = validation.load_json(path)
            self.assertIsInstance(loaded['state_seq'], Decimal)
            self.assertEqual(loaded['state_seq'].as_tuple().exponent, 1000000)
            self.assertEqual(validation.validate_state_obj(loaded), [])

    def test_json_loader_preserves_large_integer_delta_equality(self):
        with tempfile.TemporaryDirectory(prefix="cbg-exact-json-") as directory:
            path = Path(directory) / "delta.json"
            sequence = 9007199254740993
            for snapshot_seq in (sequence, sequence - 1):
                with self.subTest(snapshot_seq=snapshot_seq):
                    text = json.dumps(delta(sequence, snapshot_seq)).replace('"seq": 9007199254740993', '"seq": 9007199254740993.0')
                    path.write_text(text, encoding="utf-8")
                    errors = validation.validate_delta_obj(validation.load_json(path))
                    self.assertEqual(bool(errors), snapshot_seq != sequence)


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
        for text in ("", "## Other\nbody\n"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.select(text)

    def test_indented_atx_headings_end_the_previous_section(self):
        for indent in ("", " ", "  ", "   "):
            with self.subTest(indent=indent):
                text = f"## Target\nalpha beta gamma delta epsilon\n{indent}## Next\nwrong section tail belongs elsewhere\n"
                selected = self.select(text)
                self.assertEqual(selected[:3], ("## Target", 1, 2))
                self.assertEqual(proof.first_last_five(selected[3])[1],
                                 ["##", "Target", "alpha", "beta", "gamma", "delta", "epsilon"])

    def test_empty_atx_heading_ends_the_previous_section(self):
        for ending in ("##", "   ##", "##\t", "## ###"):
            with self.subTest(ending=ending):
                self.assertEqual(self.select(f"## Target\nbody\n{ending}\nnext body\n")[:3],
                                 ("## Target", 1, 2))

    def test_indented_and_closed_heading_selected_by_text_preserves_exact_heading(self):
        for heading in ("   ## Target", " ## Target ###", "##\tTarget\t###\t"):
            with self.subTest(heading=heading):
                text = f"{heading}\nbody\n## Next\n"
                for selector in ("Target", heading):
                    self.assertEqual(self.select(text, selector)[:3], (heading, 1, 2))

    def test_non_atx_lines_do_not_end_a_section(self):
        for line in ("    ## code indentation", "##no-space", "####### too-many", "##\u00a0not-a-separator"):
            with self.subTest(line=line):
                self.assertEqual(self.select(f"## Target\nbody\n{line}\nstill body\n## Next\n")[:3],
                                 ("## Target", 1, 4))

    def test_heading_selection_accepts_crlf_without_returning_carriage_return(self):
        text = "## Target\r\nbody\r\n## Next\r\n"
        self.assertEqual(self.select(text)[:3], ("## Target", 1, 2))

    def test_literal_hashes_in_heading_text_are_preserved(self):
        for heading, selector in (("## C#", "C#"), ("## Target###", "Target###"),
                                  ("## Target \\###", "Target \\###")):
            with self.subTest(heading=heading):
                self.assertEqual(self.select(f"{heading}\nbody\n## Next\n", selector)[:3],
                                 (heading, 1, 2))


class CliAndFiles(unittest.TestCase):
    def run_script(self, name, directory, *arguments):
        return subprocess.run([sys.executable, "-B", "-X", "utf8", str(BUNDLE / "scripts" / name), *map(str, arguments)],
                              cwd=directory, capture_output=True, text=True, encoding="utf-8")

    def test_proof_cli_distinguishes_no_lines_from_existing_blank_lines(self):
        cases = [(b"", None, 0), (b"\xef\xbb\xbf", None, 0),
                 (b"\n", [1, 1], 0), (b" \n\n", [1, 2], 0),
                 (b"one", [1, 1], 1)]
        with tempfile.TemporaryDirectory(prefix="cbg-empty-proof-") as directory:
            path = Path(directory) / "source.md"
            for data, span, word_count in cases:
                with self.subTest(data=data):
                    path.write_bytes(data)
                    result = self.run_script("extract_proof.py", directory, path, "--json")
                    self.assertEqual(result.returncode, 0, result.stderr)
                    report = json.loads(result.stdout)
                    self.assertEqual(report["source"], str(path))
                    self.assertEqual(report["heading"], "FULL_FILE")
                    self.assertEqual(report["line_range"], span)
                    self.assertEqual(report["word_count"], word_count)
                    self.assertEqual(report["first_5_words"], ["one"] if word_count else [])
                    self.assertEqual(report["last_5_words"], ["one"] if word_count else [])
                    plain = self.run_script("extract_proof.py", directory, path)
                    self.assertEqual(plain.returncode, 0, plain.stderr)
                    expected = "none (empty file)" if span is None else f"{span[0]}-{span[1]}"
                    self.assertIn("line_range: " + expected, plain.stdout.splitlines())
                    self.assertEqual(path.read_bytes(), data)

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

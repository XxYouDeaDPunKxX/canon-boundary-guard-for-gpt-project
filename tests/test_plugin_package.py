"""Exercise the ChatGPT package and shipped helpers through real files/CLIs."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_PATH = Path("plugin/canon-boundary-guard")
SKILL_PATH = PLUGIN_PATH / "skills/canon-boundary-guard"

class NativePluginPackage(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="cbg-native-package-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for path in (PLUGIN_PATH, Path("canon-boundary-guard-gpt")):
            shutil.copytree(ROOT / path, self.root / path)
        (self.root / "tools").mkdir()
        for path in (Path("tools/package_plugin.py"), Path("LICENSE")):
            shutil.copyfile(ROOT / path, self.root / path)
        self.skill = self.root / SKILL_PATH

    def build(self):
        return subprocess.run([sys.executable, "-B", str(self.root / "tools/package_plugin.py")],
                              cwd=self.root, capture_output=True, text=True, encoding="utf-8")

    def built_archive(self):
        result = self.build()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return Path(json.loads(result.stdout)["archive"])

    def test_archive_contains_only_the_current_chat_skill_and_its_resources(self):
        prefix = "canon-boundary-guard/"
        skill = prefix + "skills/canon-boundary-guard/"
        expected = {prefix + name for name in ("plugin.json", "LICENSE", "README.md")}
        expected.update(skill + name for name in ("SKILL.md", "agents/openai.yaml",
                        "scripts/extract_proof.py", "scripts/artifact_fingerprint.py"))
        with zipfile.ZipFile(self.built_archive()) as archive:
            self.assertEqual(set(archive.namelist()), expected)
            self.assertIsNone(archive.testzip())

    def test_one_complete_instruction_document(self):
        self.assertEqual({p.relative_to(self.skill).as_posix() for p in self.skill.rglob("*.md")}, {"SKILL.md"})
        text = (self.skill / "SKILL.md").read_text(encoding="utf-8")
        for obsolete in ("SESSION_STATE", "CANON_STATE_DELTA", "SESSION_INSTRUCTIONS",
                         "PROJECT_CUSTOM_INSTRUCTIONS", "Project Sources", "Project Instructions",
                         "gpt-project-adapter", "fresh install"):
            with self.subTest(obsolete=obsolete):
                self.assertNotIn(obsolete, text)

    def test_extracted_helpers_preserve_unicode_paths_and_text_in_utf8_runtime(self):
        extracted = self.root / "extracted"
        with zipfile.ZipFile(self.built_archive()) as archive:
            archive.extractall(extracted)
        scripts = extracted / "canon-boundary-guard/skills/canon-boundary-guard/scripts"
        source = self.root / "source-\U0001f9ea.md"
        source.write_bytes("# Caf\u00e9 \u6771\u4eac \U0001f9ea\none two three four five six seven eight nine ten\n".encode("utf-8"))

        def run(name, *args):
            # UTF-8 execution contract; this local test is not Linux host evidence.
            result = subprocess.run([sys.executable, "-B", "-X", "utf8", str(scripts / name),
                                     *map(str, args)], cwd=self.root, capture_output=True,
                                    text=True, encoding="utf-8")
            self.assertEqual(result.returncode, 0, result.stderr)
            return result.stdout

        proof = json.loads(run("extract_proof.py", source, "--json"))
        self.assertEqual(proof["source"], str(source))
        self.assertEqual(proof["first_5_words"], ["#", "Caf\u00e9", "\u6771\u4eac", "\U0001f9ea", "one"])
        self.assertEqual(proof["last_5_words"], ["six", "seven", "eight", "nine", "ten"])
        self.assertEqual(proof["line_range"], [1, 2])
        self.assertIn("first_5_words: # Caf\u00e9 \u6771\u4eac \U0001f9ea one", run("extract_proof.py", source))
        record = json.loads(run("artifact_fingerprint.py", source))[0]
        self.assertEqual(record["path"], str(source))
        self.assertEqual(record["sha256"], hashlib.sha256(source.read_bytes()).hexdigest())

    def test_build_rejects_an_obsolete_extra_entrypoint(self):
        (self.skill / "PROJECT_CUSTOM_INSTRUCTIONS.txt").write_text("obsolete entrypoint", encoding="utf-8")
        self.assertNotEqual(self.build().returncode, 0)

    def test_build_accepts_windows_skill_line_endings(self):
        path = self.skill / "SKILL.md"
        path.write_bytes(path.read_text(encoding="utf-8").replace("\n", "\r\n").encode("utf-8"))
        self.built_archive()

    def test_build_rejects_a_broken_resource_reference(self):
        for link in ("`references/missing.md`", "[proof](scripts/missing.py)"):
            with self.subTest(link=link):
                path = self.skill / "SKILL.md"
                before = path.read_bytes()
                path.write_text(path.read_text(encoding="utf-8") + "\nRead " + link + ".\n", encoding="utf-8")
                self.assertNotEqual(self.build().returncode, 0)
                path.write_bytes(before)

    def test_build_rejects_reintroduced_session_dependency(self):
        with (self.skill / "SKILL.md").open("a", encoding="utf-8") as stream:
            stream.write("\nBefore working, require SESSION_STATE.json.\n")
        self.assertNotEqual(self.build().returncode, 0)

    def test_build_rejects_helper_copy_drift(self):
        with (self.skill / "scripts/extract_proof.py").open("a", encoding="utf-8") as stream:
            stream.write("\n# Unsynchronized helper change\n")
        self.assertNotEqual(self.build().returncode, 0)

    def test_extracted_helpers_work_without_state_or_schemas_from_another_directory(self):
        extracted = self.root / "extracted"
        with zipfile.ZipFile(self.built_archive()) as archive:
            archive.extractall(extracted)
        scripts = extracted / "canon-boundary-guard/skills/canon-boundary-guard/scripts"
        source = self.root / "source.md"
        source.write_text("   ## Target ###\none two three four five six seven eight nine ten\n  ## Next\nend\n",
                          encoding="utf-8-sig")
        result = subprocess.run([sys.executable, "-B", str(scripts / "extract_proof.py"),
                                 str(source), "--heading", "Target", "--json"], cwd=self.root,
                                capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        proof = json.loads(result.stdout)
        self.assertEqual(proof["heading"], "   ## Target ###")
        self.assertEqual(proof["line_range"], [1, 2])
        self.assertEqual(proof["last_5_words"], ["six", "seven", "eight", "nine", "ten"])
        result = subprocess.run([sys.executable, "-B", str(scripts / "artifact_fingerprint.py"),
                                 str(source), str(self.root / "absent.md")], cwd=self.root,
                                capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)
        records = json.loads(result.stdout)
        self.assertEqual(records[0]["sha256"], hashlib.sha256(source.read_bytes()).hexdigest())
        self.assertFalse(records[1]["exists"])
        self.assertFalse((scripts.parent / "schemas").exists())

    def test_repeated_builds_have_identical_bytes(self):
        first = self.built_archive().read_bytes()
        self.assertEqual(self.built_archive().read_bytes(), first)

    def test_extracted_proof_reports_no_line_range_for_an_empty_file(self):
        extracted = self.root / "extracted"
        with zipfile.ZipFile(self.built_archive()) as archive:
            archive.extractall(extracted)
        script = extracted / "canon-boundary-guard/skills/canon-boundary-guard/scripts/extract_proof.py"
        source = self.root / "empty.md"
        source.write_bytes(b"")
        for mode in (("--json",), ()):
            with self.subTest(mode=mode):
                result = subprocess.run([sys.executable, "-B", str(script), str(source), *mode],
                                        cwd=self.root, capture_output=True, text=True, encoding="utf-8")
                self.assertEqual(result.returncode, 0, result.stderr)
                if mode:
                    report = json.loads(result.stdout)
                    self.assertIsNone(report["line_range"])
                    self.assertEqual(report["word_count"], 0)
                    self.assertEqual(report["first_5_words"], [])
                    self.assertEqual(report["last_5_words"], [])
                else:
                    self.assertIn("line_range: none (empty file)", result.stdout.splitlines())

if __name__ == "__main__":
    unittest.main()

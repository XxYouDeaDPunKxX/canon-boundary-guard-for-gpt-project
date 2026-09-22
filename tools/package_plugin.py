"""Check conversion fidelity and create the private ChatGPT upload ZIP.

Run from any directory: python tools/package_plugin.py
Uses only the Python standard library; never changes the original sources.
"""

from pathlib import Path, PurePosixPath
import difflib
import hashlib
import json
import re
import stat
import unicodedata
import zipfile


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugin/canon-boundary-guard"
SOURCE = ROOT / "canon-boundary-guard-gpt"
SKILL = PLUGIN / "skills/canon-boundary-guard-gpt-project"
DIST = ROOT / "dist"
START_PREFIX = (
    "Use at the start of every ChatGPT conversation or Project session, before "
    "the first substantive output, and throughout the session as the active "
    "Canon Boundary Guard posture. "
)
BINDING_START = b"## Native plugin binding\n\n"
BINDING_END = b"<!-- End native plugin binding; original skill body follows unchanged. -->\n\n"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def main():
    original = (SOURCE / "SKILL.md").read_bytes()
    converted = (SKILL / "SKILL.md").read_bytes()
    require(converted.count(BINDING_START) == 1, "Expected one native binding")
    require(converted.count(BINDING_END) == 1, "Expected one binding end")
    start = converted.index(BINDING_START)
    end = converted.index(BINDING_END) + len(BINDING_END)
    restored = converted[:start] + converted[end:]
    prefix = b"description: " + START_PREFIX.encode("utf-8")
    require(restored.count(prefix) == 1, "Missing session-start description")
    restored = restored.replace(prefix, b"description: ", 1)
    require(restored == original, "Original SKILL content changed beyond the binding and description")

    mappings = [(p, SKILL / p.relative_to(SOURCE)) for p in sorted(SOURCE.rglob("*"))
                if p.is_file() and p.name != "SKILL.md"]
    mappings += [(ROOT / "PROJECT_CUSTOM_INSTRUCTIONS.txt", SKILL / "PROJECT_CUSTOM_INSTRUCTIONS.txt"),
                 (ROOT / "LICENSE", PLUGIN / "LICENSE")]
    copies = []
    for source, target in mappings:
        data = source.read_bytes()
        require(data == target.read_bytes(), f"Source copy differs: {target}")
        copies.append({"source": source.relative_to(ROOT).as_posix(),
                       "target": target.relative_to(PLUGIN).as_posix(), "sha256": sha256(data)})

    native = json.loads((PLUGIN / "plugin.json").read_text(encoding="utf-8"))
    compat = json.loads((PLUGIN / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    require(native["$schema"] == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json", "Wrong manifest schema")
    for key in ("name", "version", "description", "author", "repository", "license"):
        require(native[key] == compat[key], f"Manifests disagree on {key}")
    require(native["extensions"]["com.openai"]["interface"] == compat["interface"], "Interface mismatch")
    require(native["name"] == PLUGIN.name, "Plugin directory/name mismatch")
    require(compat["skills"] == "./skills/", "Wrong skill directory")
    require(re.fullmatch(r"[a-z0-9-]{1,64}", native["name"]), "Invalid plugin name")
    require(re.fullmatch(r"\d+\.\d+\.\d+", native["version"]), "Invalid version")
    require(len(native["description"]) <= 1024, "Plugin description too long")
    frontmatter = converted.decode("utf-8").split("---", 2)[1]
    skill_name = re.search(r"^name: (.+)$", frontmatter, re.M).group(1)
    description = re.search(r"^description: (.+)$", frontmatter, re.M).group(1)
    require(skill_name == SKILL.name, "Skill name/directory mismatch")
    require(len(f"{native['name']}:{skill_name}") <= 64, "Qualified skill name too long")
    require(len(description) <= 1024, "Skill description too long")

    paths = sorted(PLUGIN.rglob("*"))
    require(not any(p.is_symlink() for p in paths), "Symlinks cannot be packaged")
    files = [p for p in paths if p.is_file()]
    expected = {t.relative_to(PLUGIN).as_posix() for _, t in mappings}
    expected.update({"plugin.json", ".codex-plugin/plugin.json", "README.md",
                     "skills/canon-boundary-guard-gpt-project/SKILL.md",
                     "skills/canon-boundary-guard-gpt-project/agents/openai.yaml"})
    require({p.relative_to(PLUGIN).as_posix() for p in files} == expected, "Unexpected or missing package files")
    inventory = {}
    names = set()
    for path in files:
        name = f"{PLUGIN.name}/{path.relative_to(PLUGIN).as_posix()}"
        parts = PurePosixPath(name).parts
        require(not name.startswith("/") and "\\" not in name and ".." not in parts, "Unsafe ZIP path")
        require(len(parts) <= 20, "ZIP path too deep")
        normalized = unicodedata.normalize("NFC", name).casefold()
        require(normalized not in names, "Duplicate normalized ZIP entry")
        names.add(normalized)
        inventory[name] = sha256(path.read_bytes())
    require(len(files) <= 5000, "Too many ZIP entries")
    require(sum(p.stat().st_size for p in files) <= 512 * 1024 * 1024, "Uncompressed package too large")

    DIST.mkdir(exist_ok=True)
    archive = DIST / f"{native['name']}-{native['version']}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as output:
        for path in files:
            name = f"{PLUGIN.name}/{path.relative_to(PLUGIN).as_posix()}"
            info = zipfile.ZipInfo(name, date_time=(2026, 9, 22, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            output.writestr(info, path.read_bytes())
    require(archive.stat().st_size <= 100 * 1024 * 1024, "Compressed ZIP too large")
    with zipfile.ZipFile(archive) as zipped:
        require(zipped.testzip() is None, "ZIP integrity check failed")
        require(zipped.namelist() == list(inventory), "ZIP inventory mismatch")
        for name, digest in inventory.items():
            require(sha256(zipped.read(name)) == digest, f"ZIP content mismatch: {name}")

    diff = "".join(difflib.unified_diff(original.decode("utf-8").splitlines(keepends=True),
                                       converted.decode("utf-8").splitlines(keepends=True),
                                       fromfile="original/canon-boundary-guard-gpt/SKILL.md",
                                       tofile="plugin/skills/canon-boundary-guard-gpt-project/SKILL.md"))
    (DIST / "SKILL.diff").write_text(diff, encoding="utf-8", newline="\n")
    report = {"plugin": native["name"], "version": native["version"],
              "archive": archive.name, "archive_sha256": sha256(archive.read_bytes()),
              "archive_bytes": archive.stat().st_size, "byte_identical_copies": copies,
              "skill_original_sha256": sha256(original), "skill_converted_sha256": sha256(converted),
              "original_skill_reconstructed_exactly": True, "archive_files": inventory,
              "chatgpt_import_tested": False, "chatgpt_session_start_tested": False}
    (DIST / "manifest.sha256.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"archive": str(archive), "files": len(files),
                      "byte_identical_copies": len(copies), "skill_fidelity": "passed",
                      "archive_bytes": archive.stat().st_size, "archive_sha256": report["archive_sha256"]}, indent=2))


if __name__ == "__main__":
    main()

"""Validate resources and build the personal ChatGPT plugin ZIP.

Run from any directory: python tools/package_plugin.py
Does not modify source bundles, plugin resources, accounts, or remote repositories.
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
SKILL = PLUGIN / "skills/canon-boundary-guard"
DIST = ROOT / "dist"
SOURCE = ROOT / "canon-boundary-guard-gpt"

# Only resources still shipped as exact copies belong in this mapping.
RESOURCE_SOURCES = {
    "skills/canon-boundary-guard/scripts/artifact_fingerprint.py":
        "canon-boundary-guard-gpt/scripts/artifact_fingerprint.py",
    "skills/canon-boundary-guard/scripts/extract_proof.py":
        "canon-boundary-guard-gpt/scripts/extract_proof.py",
    "LICENSE": "LICENSE",
}
INSTRUCTION_SOURCES = [
    "SKILL.md", "references/protocol.md", "references/gpt-project-adapter.md",
    "references/proof-of-read.md", "references/scratch-canon.md",
]
RESOURCE_LINK = re.compile(r"(?<![\w/])(?:references|schemas|scripts|agents)/[A-Za-z0-9_./-]+")
RETIRED_RUNTIME = re.compile(
    r"SESSION_STATE|CANON_STATE_DELTA|SESSION_INSTRUCTIONS|PROJECT_CUSTOM_INSTRUCTIONS|"
    r"gpt-project-adapter|Project Sources|Project Instructions|fresh install", re.I)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def main():
    records = []
    for relative, source_relative in RESOURCE_SOURCES.items():
        source, target = ROOT / source_relative, PLUGIN / relative
        before, after = source.read_bytes(), target.read_bytes()
        require(before == after, f"Source copy differs: {target}")
        records.append({"source": source_relative, "target": relative, "mode": "identical",
                        "source_sha256": sha256(before), "target_sha256": sha256(after)})

    converted = (SKILL / "SKILL.md").read_bytes()
    text = converted.decode("utf-8")
    require(not RETIRED_RUNTIME.search(text), "Retired session/Project dependency in native instructions")
    require({p.relative_to(SKILL).as_posix() for p in SKILL.rglob("*.md")} == {"SKILL.md"},
            "The complete posture must have one instruction entrypoint")
    inspected_links = []
    for relative in sorted(set(RESOURCE_LINK.findall(text))):
        relative = relative.rstrip(".")
        target = (SKILL / relative).resolve()
        require(target.is_relative_to(SKILL.resolve()) and target.is_file(),
                f"Unresolved resource reference: {relative}")
        inspected_links.append({"document": "SKILL.md", "resource": relative})

    native = json.loads((PLUGIN / "plugin.json").read_text(encoding="utf-8"))
    require(native["$schema"] == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
            "Wrong manifest schema")
    require(native["name"] == PLUGIN.name, "Plugin directory/name mismatch")
    require(re.fullmatch(r"[a-z0-9-]{1,64}", native["name"]), "Invalid plugin name")
    require(re.fullmatch(r"\d+\.\d+\.\d+", native["version"]), "Invalid version")
    require(len(native["description"]) <= 1024, "Plugin description too long")
    normalized = "\n".join(text.splitlines())
    require(normalized.startswith("---\n"), "Missing skill frontmatter")
    sections = normalized.split("---", 2)
    require(len(sections) == 3 and sections[2].strip(), "Missing skill body")
    frontmatter = sections[1]
    name_match = re.search(r"^name: (.+)$", frontmatter, re.M)
    description_match = re.search(r"^description: (.+)$", frontmatter, re.M)
    require(name_match and description_match, "Missing skill name or description")
    skill_name, description = name_match.group(1), description_match.group(1)
    require(skill_name == SKILL.name, "Skill name/directory mismatch")
    require(len(f"{native['name']}:{skill_name}") <= 64, "Qualified skill name too long")
    require(0 < len(description) <= 1024, "Invalid skill description length")

    paths = sorted(PLUGIN.rglob("*"))
    require(not any(path.is_symlink() for path in paths), "Symlinks cannot be packaged")
    files = [path for path in paths if path.is_file()]
    expected = set(RESOURCE_SOURCES)
    expected.update({"plugin.json", "README.md", "skills/canon-boundary-guard/SKILL.md",
                     "skills/canon-boundary-guard/agents/openai.yaml"})
    require({path.relative_to(PLUGIN).as_posix() for path in files} == expected,
            "Unexpected or missing package files")
    inventory, names = {}, set()
    for path in files:
        name = f"{PLUGIN.name}/{path.relative_to(PLUGIN).as_posix()}"
        parts = PurePosixPath(name).parts
        require(not name.startswith("/") and "\\" not in name and ".." not in parts, "Unsafe ZIP path")
        require(len(parts) <= 20, "ZIP path too deep")
        normalized_name = unicodedata.normalize("NFC", name).casefold()
        require(normalized_name not in names, "Duplicate normalized ZIP entry")
        names.add(normalized_name)
        inventory[name] = sha256(path.read_bytes())
    require(len(files) <= 5000, "Too many ZIP entries")
    require(sum(path.stat().st_size for path in files) <= 512 * 1024 * 1024, "Uncompressed package too large")

    DIST.mkdir(exist_ok=True)
    archive = DIST / f"{native['name']}-{native['version']}.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as output:
        for path in files:
            name = f"{PLUGIN.name}/{path.relative_to(PLUGIN).as_posix()}"
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
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

    original = (SOURCE / "SKILL.md").read_bytes()
    skill_diff = "".join(difflib.unified_diff(original.decode("utf-8").splitlines(keepends=True),
                                             text.splitlines(keepends=True),
                                             fromfile="source/SKILL.md", tofile="native/SKILL.md"))
    (DIST / "SKILL.diff").write_text(skill_diff, encoding="utf-8", newline="\n")
    report = {"plugin": native["name"], "version": native["version"],
              "archive": archive.name, "archive_sha256": sha256(archive.read_bytes()),
              "archive_bytes": archive.stat().st_size, "source_mapping": records,
              "consolidated_instruction_sources": [
                  {"source": (SOURCE / p).relative_to(ROOT).as_posix(),
                   "sha256": sha256((SOURCE / p).read_bytes())} for p in INSTRUCTION_SOURCES],
              "runtime_scope": "current conversation; no cross-conversation state subsystem",
              "resolved_resource_links": inspected_links, "archive_files": inventory,
              "chatgpt_import_tested": False, "chatgpt_session_start_tested": False}
    (DIST / "manifest.sha256.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"archive": str(archive), "files": len(files),
                      "byte_identical_resources": len(records),
                      "resolved_resource_links": len(inspected_links),
                      "archive_bytes": archive.stat().st_size, "archive_sha256": report["archive_sha256"]}, indent=2))


if __name__ == "__main__":
    main()

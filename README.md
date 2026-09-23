<p align="center">
  <img src="./assets/ChatGPT Image 23 mag 2026, 19_38_50.png" alt="ChatGPT Image 23 mag 2026, 19_38_50" width="100%">
</p>

# 🛡️ Canon Boundary Guard

Canon Boundary Guard is a provenance posture for ChatGPT. It keeps inspected
sources, conversation material, authorized changes, instructions to the
assistant, and unverified assumptions distinguishable before they enter
reusable answers or artifacts.

This repository provides two formats:

| Format | Where to use it | What it includes |
| --- | --- | --- |
| [ChatGPT plugin](plugin/canon-boundary-guard/README.md) · **0.3.2** | ChatGPT web conversations | One complete skill and two optional Python helpers. Operates within the current conversation, without session-state or recovery files. |
| [GPT Project bundle](canon-boundary-guard-gpt/SKILL.md) | A ChatGPT Project, with Project instructions | The original source bundle, including its state, schema, and recovery workflow. |

The plugin carries the posture into ordinary web chats. The Project bundle
retains its original operating rules; shared helper fixes apply to both formats.

## 🔎 What It Does

In a long session, many things can start looking equally important:

- files attached to a chat or Project
- things said in the current chat
- older project memory or moved chats
- instructions that tell ChatGPT how to behave
- assumptions made by the model
- drafts generated during the session

Canon Boundary Guard applies throughout the conversation, from the first
substantive response. Its checks become visible when material is about to cross
into reusable output.

The main goal is simple: a chat message, draft, assumption, or generated file
should not silently become canon.

## 📦 Install

### ChatGPT web plugin

1. Download or clone this repository, then run `python tools/package_plugin.py`
   from its root.
2. In ChatGPT web, open the plugin creation dialog from the Plugins page and upload
   `dist/canon-boundary-guard-0.3.2.zip`.
3. Complete the add-plugin flow. Activate Canon Boundary Guard through your
   ChatGPT custom instructions or explicitly select/tag the plugin in the first
   message of a new conversation.

For custom instructions, use:

> Use Canon Boundary Guard from the start of every conversation. Read its complete
> skill before the first substantive response and apply it throughout the chat.

Upload the generated plugin archive. Once loaded, the complete posture stays
active throughout the conversation; no initialization declaration or state file
is needed. The package description is not a session-start hook, so installation
alone does not establish that the skill was loaded. See the
[plugin README](plugin/canon-boundary-guard/README.md) for scope and verification.

### GPT Project bundle

1. Create a ZIP containing the `canon-boundary-guard-gpt/` folder.
2. Add that ZIP to your ChatGPT Project files or sources.
3. Copy [PROJECT_CUSTOM_INSTRUCTIONS.txt](PROJECT_CUSTOM_INSTRUCTIONS.txt) into
   the Project instructions.
4. Start a new chat inside the Project.

The ZIP contains the frame. The Project instructions tell ChatGPT to open it,
inspect it, and use it for the session. The bundle's state and recovery rules
remain part of this format; see the technical notes below.

For manual use of the source bundle in an ordinary chat, upload the same ZIP and
ask ChatGPT to inspect it and use it as the active frame. That puts the instruction
anchor inside the conversation instead of the Project instructions.

## ▶️ Use

Use the Project or chat normally.

With the plugin, ChatGPT reads the complete skill; with the Project bundle, it
inspects the bundle required by the Project instructions. In both cases, it
should separate:

- inspected evidence
- chat material
- operator-approved changes
- agent-control instructions
- model assumptions

For ordinary conversation, it should stay quiet.

It should surface when something starts crossing a boundary: a hypothesis starts
acting like a premise, a draft starts acting like a decision, or content is being
prepared for a reusable answer, file, document, or Canvas output. The Project
bundle also checks Project Source promotion and state or recovery operations.

## ⚠️ Limits

Both formats are documentary instructions. They define what should be
recognized as canon; they cannot enforce every answer, save, file action, or UI
action. ChatGPT can still skip instructions, lose context, or fail to inspect a
source.

The plugin carries no decision record between conversations. The Project
bundle's working state is not durable by itself and requires its explicit
recovery workflow. Neither format guarantees correctness.

## 🤖 AI-assisted development

This project was developed with AI assistance.

The project, documentation, and repository materials were shaped through
human-directed work supported by AI tools during drafting, structuring, review,
and refinement.

AI assistance does not make the project automatically correct, complete, or
suitable for every use case. Read it, test it, and adapt it to your own context.

## 📜 License

This project is licensed under CC BY-SA 4.0: Creative Commons
Attribution-ShareAlike 4.0 International.

See [LICENSE](LICENSE).

<details>
<summary>⚙️ Technical notes</summary>

## 🧱 Package Structure

The ChatGPT plugin packages these seven files:

```text
plugin/canon-boundary-guard/
|-- plugin.json
|-- LICENSE
|-- README.md
`-- skills/canon-boundary-guard/
    |-- SKILL.md
    |-- agents/openai.yaml
    `-- scripts/
        |-- extract_proof.py
        `-- artifact_fingerprint.py
```

Its complete posture is in one
[SKILL.md](plugin/canon-boundary-guard/skills/canon-boundary-guard/SKILL.md).
The metadata targets ChatGPT `CHAT`. It ships no state validator, state schemas,
Project instruction anchor, or recovery subsystem.

The original Project bundle uses
[PROJECT_CUSTOM_INSTRUCTIONS.txt](PROJECT_CUSTOM_INSTRUCTIONS.txt) as its
instruction anchor and contains:

```text
canon-boundary-guard-gpt/
|-- SKILL.md
|-- references/
|   |-- gpt-project-adapter.md
|   |-- proof-of-read.md
|   |-- protocol.md
|   |-- scratch-canon.md
|   `-- state-and-recovery.md
|-- schemas/
|   |-- CANON_STATE_DELTA.schema.json
|   `-- SESSION_STATE.schema.json
`-- scripts/
    |-- artifact_fingerprint.py
    |-- extract_proof.py
    `-- validate_state.py
```

## 🧭 Project Bundle Details

The following source classes, gate labels, extraction rules, and state workflow
describe the **Project bundle**. The plugin's conversation-scoped rules are
defined in its own skill linked above.

The Project operating model is:

- upload the zipped source bundle to the Project
- paste `PROJECT_CUSTOM_INSTRUCTIONS.txt` into Project instructions
- require ChatGPT to locate and inspect the bundle before substantive work
- use the bundle as the active provenance-control frame
- treat Project files, `/mnt/data`, and saved material as evidence only after
  current-task inspection

### Source classes

The frame separates source classes:

- `L0`: inspected evidence
- `L1`: chat material and project memory, not canon
- `L1A`: operator-approved delta in the current turn
- `L2`: agent-control instructions
- `L3`: unverified model prior

A Project Source is `L0` only for the relevant surface inspected in the current
task. Presence in Project files is not evidence by itself.

### Simulated gate

The Project adapter implements its gate through instructions at the semantic
persistence boundary, without an executable pre-write hook.

The gate is required before:

- downloadable final artifacts
- Canvas or document output intended for reuse
- Project Source candidates
- reusable specs, workflows, naming rules, protocols, or policies
- state or recovery operations
- promotion from scratch to canon/final output
- any output marked `[SAFE TO SAVE]`

Labels are deterministic:

```text
[SAFE TO SAVE]
[DO NOT SAVE - L1/L3 PRESENT]
[STATE DELTA - SAVE/PASTE ONLY AS RECOVERY MATERIAL]
[DRAFT - REQUIRES OPERATOR APPROVAL]
```

### Source-staged extraction

If the bundle zip is available only inside `/mnt/data`, it can be extracted as a
source-staged extraction.

That extracted copy may support `L0` inspection only as a mechanical view of the
uploaded or Project Source zip it came from.

Before treating extracted files as `L0`, the assistant should record the source
zip path or source id, and hash if available. If no anchor is available, it must
declare the missing anchor and limit `L0` to the inspected path with a risk note.

Assistant-generated scratch artifacts remain non-evidence.

### State and recovery

Working state path:

```text
/mnt/data/_SESSION_STATE.json
```

This file is not durable by itself.

First-install state may be created only when the operator declares a fresh
install, or when the task is initial bundle installation and there is no
prior-state claim.

The first-install state must record the inspected bootstrap surfaces in
`active_l0_sources`. A schema-minimal state with an empty `active_l0_sources`
array is not a first-install template.

Outside first install, if valid state is unavailable, the adapter enters
read-only recovery mode.

Recovery sources:

1. uploaded `SESSION_STATE.json`
2. pasted `CANON_STATE_DELTA` with valid `current_state`
3. explicit operator reconstruction marked as `L1A`

## 🧪 Helpers and Verification

The Python scripts are optional mechanical helpers. They are not hooks and do
not decide provenance.

Both formats include identical copies of:

- `extract_proof.py`: extracts mechanical proof-of-read from text or Markdown,
  reading with `utf-8-sig`. An input with no text lines has `line_range: null`.
- `artifact_fingerprint.py`: emits file size, modified time, and SHA-256.

These two helpers use only Python's standard library and can run on accessible
files in ChatGPT's Python environment.

Only the Project bundle includes `validate_state.py`, which validates
`SESSION_STATE` and `CANON_STATE_DELTA` files:

- uses `jsonschema` when available
- falls back to strict manual validation
- reads JSON with `utf-8-sig`
- fails closed when a required schema feature cannot be checked

### Repository checks

Run `python -B -m unittest discover -s tests -v` from the repository root.
To exercise the optional `jsonschema` branch as well as the manual fallback,
install `requirements-test.txt` in your test environment first. Without it,
the suite explicitly skips the tests that require that library.

The regressions cover JSON sequence validation, Markdown headings and fenced
code, the ten-word proof boundary, empty and BOM-only input, relocated schema
paths, and file fingerprints.

The native package tests extract its ZIP and execute both shipped helpers from
an unrelated working directory, without state files or schemas. The state tests
apply only to the original source bundle.

Run `python -B -X utf8 tools/verify_plugin.py` to run the suite, build the plugin,
and audit its helpers together. The runner writes test logs, an archive manifest,
and results for the exact package bytes into the local `dist/` directory.
`python tools/package_plugin.py` builds only the package and checks its inventory,
helper copies, resource references, and archive contents.

These checks verify code and packaging. They do not establish ChatGPT's loading
or instruction-following behavior; those require a conversation with the
installed plugin activated through custom instructions or an explicit tag.

</details>

---
name: canon-boundary-guard-gpt-project
description: Apply Canon Boundary Guard provenance control in ChatGPT Projects before persistent writes, generated artifacts, Project Sources, Project Instructions, Canvas or document outputs, /mnt/data scratch-to-canon promotion, save labels, state or recovery operations, and proof-of-read checks. Use whenever shaping rules, protocols, architecture, naming, workflow expectations, session state, or reusable project content.
---

# Canon Boundary Guard for GPT Projects

Use this skill to keep project content separated from conversation residue, agent-control instructions, model assumptions, and unverified memory.

This package adapts the original Canon Boundary Guard frame to GPT Projects. It does not rely on Codex hooks or Claude skill execution. It uses a simulated persistence gate, project sources, explicit state, deterministic labels, and optional Python validators.

## Operating rule

Before persistent output, classify provenance and run the simulated gate.

Persistent output includes:
- Project Instructions
- Project Sources
- reusable specs, policies, workflows, naming rules, architecture, or protocols
- Canvas or document output intended for reuse
- downloadable final artifacts
- promotion from `/mnt/data/scratch/**` to `/mnt/data/canon/**`
- state or recovery material
- any response marked `[SAFE TO SAVE]`

Disposable scratch work inside `/mnt/data/scratch/**` is Mode A by default and does not require a dossier.

## Required bootstrap

Before the first substantive output in a new Project session, run Status Check:

1. Locate the `canon-boundary-guard-gpt/` bundle in Project Sources or
   `/mnt/data`.
2. If only a zip is available in `/mnt/data`, extract it first as a
   source-staged extraction.
3. If source-staged extraction is used, record the source zip path or source id,
   and hash if available, before treating extracted surfaces as L0. If no anchor
   is available, limit L0 to the inspected path with a risk note.
4. Inspect this `SKILL.md`.
5. Inspect `references/protocol.md`.
6. Inspect `references/gpt-project-adapter.md`.
7. Inspect the latest `SESSION_STATE.json` if available.
8. If no `SESSION_STATE` exists, initialize a new working state only when the
   operator declares a fresh install, or when the current task is initial bundle
   installation and there is no prior-state claim. Initialize it only after
   required sources, `references/state-and-recovery.md`, and
   `schemas/SESSION_STATE.schema.json` have been inspected. Validate it if
   `scripts/validate_state.py` is available.
   Register the inspected bootstrap surfaces in `active_l0_sources`; do not use
   an empty `active_l0_sources` array after bootstrap.
9. If persistence is requested, provide mechanical proof-of-read.

If required sources cannot be inspected, enter read-only mode and do not produce persistent output.

## Source classes

Use the full definitions in `references/protocol.md`.

- L0: inspected evidence. A Project Source is L0 only for the relevant surface
  inspected in the current task.
- L1: conversation material and project memory, not canon.
- L1A: operator-approved delta in the current turn.
- L2: agent-control instructions.
- L3: unverified model prior.

## Modes

- Mode A: mechanical L0 operation. Proceed silently.
- Mode B: semantic reorganization of L0. Use compact dossier if persistent.
- Mode C: promotion of L1/L1A/L2/L3. Use full dossier and stop unless explicitly authorized.

## References

Read only what the current task needs:

- `references/protocol.md` — provenance layers, rules, dossier, contamination checks.
- `references/gpt-project-adapter.md` — GPT Project persistence boundary, bootstrap, save labels.
- `references/state-and-recovery.md` — session state, snapshot deltas, recovery mode.
- `references/scratch-canon.md` — `/mnt/data` zones and promotion rules.
- `references/proof-of-read.md` — mechanical proof requirements.

## Schemas

Use these for state validation:

- `schemas/SESSION_STATE.schema.json`
- `schemas/CANON_STATE_DELTA.schema.json`

## Optional Python validators

Use scripts only for mechanical checks. They are not hooks and do not make decisions.

- `scripts/validate_state.py`
- `scripts/artifact_fingerprint.py`
- `scripts/extract_proof.py`

If a validator is available and the task touches state, recovery, proof-of-read, or file promotion, use it before marking output `[SAFE TO SAVE]`.

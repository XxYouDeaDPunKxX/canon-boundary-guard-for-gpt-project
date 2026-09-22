# GPT Project Adapter

## Reason for adapter

Codex can inject context before write operations through PreToolUse hooks.

GPT Projects do not expose an equivalent user-defined pre-write hook.

This adapter defines a simulated PreToolUse gate at the semantic persistence boundary.

## Source-bundle model

This adapter assumes the folder `canon-boundary-guard-gpt/` is distributed as a
zip and uploaded to Project Sources.

At runtime, the assistant must locate the bundle through available Project
Source retrieval and/or `/mnt/data`.

If the bundle is present as a zip in `/mnt/data`, extract it before bootstrap
as a source-staged extraction.
The expected inspected entrypoint is:

`canon-boundary-guard-gpt/SKILL.md`

The zip, Project Source record, and `/mnt/data` file are not canon by default.
They become L0 only for the relevant surface actively inspected in the current
task.

A source-staged extraction may support L0 inspection only as a mechanical view
of the uploaded or Project Source zip it came from, anchored to source identity
or hash. Assistant-generated scratch artifacts remain non-evidence.

When source-staged extraction is used, record the source zip path or source id,
and hash if available, before treating extracted surfaces as L0. If source
identity or hash is unavailable, declare the missing anchor and limit L0 to the
inspected extracted path with a risk note.

## Mandatory re-entry bootstrap

Before the first substantive output in any new Project session, run Status Check.

Status Check requires active inspection of:
- canon-boundary-guard-gpt/SKILL.md
- canon-boundary-guard-gpt/references/protocol.md
- canon-boundary-guard-gpt/references/gpt-project-adapter.md
- source zip path/source id and hash if source-staged extraction is used, when
  available
- latest SESSION_STATE if available
- canon-boundary-guard-gpt/references/state-and-recovery.md if first-install
  state creation is needed
- canon-boundary-guard-gpt/schemas/SESSION_STATE.schema.json if first-install
  state creation is needed

Do not assume gate mechanics from memory.

If inspection fails, enter read-only mode.

If no SESSION_STATE exists, initialize a new working state at
`/mnt/data/_SESSION_STATE.json` only when the operator declares a fresh install,
or when the current task is initial bundle installation and there is no
prior-state claim. Create it only after Status Check succeeds, the state
recovery reference and SESSION_STATE schema have been inspected, and the created
state validates if `scripts/validate_state.py` is available.
Fresh-install initialization is not durable canon by itself.

If this is not a fresh install and no valid SESSION_STATE is available, enter
read-only recovery mode.

## Persistence boundary

CBG does not prevent UI saves; it controls canon recognition. Material saved
without gate may be inspected as evidence of its own contents, but remains
L1/recovery material unless later admitted through the gate.

Run the gate before:
- file writes intended as durable output
- downloadable final artifacts
- Canvas updates intended for reuse
- Project Source candidates
- reusable docs/specs/prompts
- protocol, naming, architecture, workflow, or invariant changes
- state or recovery operations
- promotion from `/mnt/data/scratch/**` to any canon/final destination
- `[SAFE TO SAVE]` output

Do not run the gate for:
- temporary scratch operations
- private calculations
- intermediate parsing
- disposable tests

## Runtime zones

`/mnt/data/scratch/**`
- disposable
- non-canon
- Mode A by default

`/mnt/data/canon/**`
- guarded candidate output
- requires gate before creation or update

`/mnt/data/_SESSION_STATE.json`
- working copy only
- not durable canon

## Save labels

Apply labels only when deterministic triggers are present.

Triggers:
- response contains a markdown code block
- response contains JSON, YAML, TOML, XML, SQL, Python, shell, or schema-like content
- response defines protocol, policy, architecture, naming, workflow, state, invariants, or operating rules
- response contains file contents intended for copy/save
- response contains Project Instructions text
- response contains GPT Project adapter text
- response contains SESSION_STATE or CANON_STATE_DELTA
- response is produced after "Promote this draft to canon"
- operator explicitly asks for final/spec/saveable/canon output
- response creates or modifies a reusable artifact specification

No-label cases:
- ordinary conversational replies
- critique
- planning
- clarification

unless one deterministic trigger is present.

Stop before final form when a deterministic trigger is present and the output
contains non-L0 material, unless the operator explicitly authorized the delta.

Labels:
- `[SAFE TO SAVE]`
- `[DO NOT SAVE - L1/L3 PRESENT]`
- `[STATE DELTA - SAVE/PASTE ONLY AS RECOVERY MATERIAL]`
- `[DRAFT - REQUIRES OPERATOR APPROVAL]`

Never mark `[SAFE TO SAVE]` unless the simulated gate passed.

# State and Recovery

## Working state

Working state path:

`/mnt/data/_SESSION_STATE.json`

This file is not durable by itself.

Durable state candidates:
- downloaded SESSION_STATE.json reuploaded later
- SESSION_STATE.json saved explicitly as Project Source
- pasted CANON_STATE_DELTA blocks used for recovery after validation

## SESSION_STATE

Schema-minimal shape only. This is not a first-install state template:

```json
{
  "protocol": "canon-boundary-guard:gpt-project-adapter",
  "protocol_version": "1.1",
  "state_seq": 0,
  "updated_at": "ISO-8601",
  "active_l0_sources": [],
  "authorized_deltas": [],
  "open_conflicts": [],
  "pending_decisions": [],
  "last_persistent_artifacts": [],
  "last_state_hash": "sha256:optional"
}
```

Validate against:

`schemas/SESSION_STATE.schema.json`

## First install

If no SESSION_STATE exists, initialize a new working state only when the
operator declares a fresh install, or when the current task is initial bundle
installation and there is no prior-state claim.

Create the working state only after the required bundle sources have been
inspected:

- `canon-boundary-guard-gpt/SKILL.md`
- `canon-boundary-guard-gpt/references/protocol.md`
- `canon-boundary-guard-gpt/references/gpt-project-adapter.md`
- `canon-boundary-guard-gpt/references/state-and-recovery.md`
- `canon-boundary-guard-gpt/schemas/SESSION_STATE.schema.json`

Register only the inspected bootstrap surfaces in `active_l0_sources`.

### First-install state content

The first-install working state must include `active_l0_sources` entries for the
inspected bootstrap surfaces:

- `canon-boundary-guard-gpt/SKILL.md`
- `canon-boundary-guard-gpt/references/protocol.md`
- `canon-boundary-guard-gpt/references/gpt-project-adapter.md`
- `canon-boundary-guard-gpt/references/state-and-recovery.md`
- `canon-boundary-guard-gpt/schemas/SESSION_STATE.schema.json`

Each entry records only the inspected surface, not the whole bundle.

If `scripts/validate_state.py` is available, validate the created working state
before treating it as available.

The initialized file at `/mnt/data/_SESSION_STATE.json` is working state only.
It becomes durable only after explicit export/reupload or Project Source save
through the simulated gate.

## CANON_STATE_DELTA

After every Mode B or Mode C state-changing decision, emit a self-contained snapshot delta.

A valid CANON_STATE_DELTA includes:
- metadata
- decision rationale
- previous state reference if available
- full `current_state` object
- `current_state` validating against SESSION_STATE.schema.json

Differential-only deltas are not valid recovery material.

Validate against:

`schemas/CANON_STATE_DELTA.schema.json`

## Recovery

Outside the first-install case, if valid SESSION_STATE is unavailable, enter
read-only mode.

Allowed:
- inspect Project Sources
- inspect uploaded files
- list missing state
- explain recovery options
- prepare a recovery plan

Forbidden:
- reconstruct state from chat memory
- infer approved decisions from prior discussion
- write persistent artifacts
- mark content `[SAFE TO SAVE]`
- perform Mode B/C persistence

Recovery sources allowed:
1. uploaded SESSION_STATE.json
2. pasted CANON_STATE_DELTA with valid current_state
3. explicit operator reconstruction marked as L1A

Invalid delta behavior:
- reject as recovery source
- treat as L1 recovery text only
- do not reconstruct state unless operator explicitly authorizes L1A reconstruction

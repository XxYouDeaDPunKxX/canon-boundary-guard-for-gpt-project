# Protocol

## Purpose

Classify provenance before information enters persistent project content.

The protocol does not decide what is canon. It makes visible what class of evidence is being used and where it is going.

## Layers

### L0 Evidence

Persistent or verified evidence inspected in the current task:
- project files or sources
- local files
- git state
- tests
- schemas
- lockfiles
- diagnostics
- command output
- tool output
- verified external source
- durable state files explicitly exported/reuploaded/saved and inspected
- canon artifacts created through the gate and later inspected

A Project Source is L0 only for the relevant surface inspected in the current
task. Presence in Project Sources is not evidence by itself.

### L1 Shaping

Conversation material not explicitly approved as durable project decision:
- current chat
- prior project chats
- moved chats
- brainstorming
- preferences not approved as protocol
- assistant analysis
- project memory
- recovery text not yet canonized

### L1A Authorized Delta

Conversation material the operator explicitly approved for persistence in the current turn.

Authorization applies only to the stated scope.

L1A becomes evidence only after written to a persistent artifact and later inspected.

### L2 Agent Control

Instructions, steering, reminders, or constraints that shape assistant behavior.

L2 is not project content. Persist it only if the operator explicitly requests agent-facing operating instructions.

### L3 Model Prior

Unverified model memory, generic best practice, assumed framework behavior, version claim, or unstated convention not grounded in inspected evidence.

## Rules

- Preserve or reorganize L0.
- Write L1A only within the explicitly approved scope.
- Do not persist L1.
- Do not persist L2 unless explicitly requested as agent-facing instruction.
- Do not persist L3 unless verified or operator-approved.
- If evidence conflicts, stop and report. Do not resolve by recency, confidence, or intuition.
- If provenance is unclear, surface it before writing.

## Inline tagging

Tag inline when producing content that draws on non-L0 material:

- `[L1]` from conversation, not approved for persistence
- `[L1A]` approved this turn, pending persistence
- `[L2]` agent control, not project content
- `[L3]` model prior, unverified

Tag only when the content would change if the source were different:
- rule
- name
- version
- claim about behavior
- workflow expectation
- architecture decision

Do not tag every word.

## Modes

### Mode A

Mechanical edit with clear L0 provenance.

No dossier.

### Mode B

Semantic edit reorganizing existing L0 evidence.

Use compact dossier if persistence is involved.

### Mode C

Promotion of L1, L1A, L2, or L3 into persistent content.

Use full dossier and stop before writing unless explicitly authorized.

## Full dossier format

Target:
Mode:
Evidence:
Authorized delta:
Rejected shaping:
Rejected model prior:
Conflicts:
Decision needed:

Write `none` when a field is empty.

Do not invent rejected items.

## Decontamination

Flag before persisting:

Conversation residue:
- as discussed
- as said before
- from the previous session
- come detto prima
- come discusso
- l'utente vuole

Agent-control residue:
- remember to
- I should
- ricordati
- devo
- non devo
- temporary instructions to the agent

Version ghosts:
- version references not present in L0

Model-prior claims:
- best practice
- standard approach
- recommended
- modern convention
- industry standard
- normally
- usually

Filesystem promotion ghosts:
- copied from scratch
- moved from scratch
- renamed into canon
- archived from scratch
- included from scratch

These are allowed only when grounded in L0, explicitly approved as L1A, or intentionally written in historical/migration context.

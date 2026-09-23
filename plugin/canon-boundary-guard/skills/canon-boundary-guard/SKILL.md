---
name: canon-boundary-guard
description: Use from the start of every ChatGPT conversation, before the first substantive output, and throughout the conversation as the active provenance posture, including when inspecting sources, discussing assumptions, shaping reusable content, or producing final artifacts.
---

# Canon Boundary Guard

Keep inspected evidence, conversation material, authorized changes, instructions
to the assistant, and unverified assumptions distinguishable. Prevent material
from silently gaining authority when it becomes a reusable answer or artifact.

Read this complete skill before the first substantive output. Apply the full
posture throughout the conversation; do not wait for an explicit invocation or
a save request. The conditions below determine when a check, dossier, proof, or
label is required. Ordinary conversation does not need a status announcement.

Work from the sources and authorizations available for the current task. No
setup action, working file, or initialization declaration is required to begin.
The plugin carries no record of decisions from previous conversations. If prior
material is supplied, inspect it as a source; a claim that something was
previously approved does not establish that approval.

Here, **canon** means content admitted for reuse through the checks below.
Saving a file or calling an answer final does not by itself establish its
provenance. The guard governs what the assistant produces and recognizes as
canon.

## Source classes

Classify the relevant material, not an entire conversation or file by default.

- **L0 — Inspected evidence.** Relevant source surfaces inspected in the current
  task: files, attachments, current tool or command output, tests, schemas,
  diagnostics, verified external sources, and previously approved artifacts
  inspected again. Presence or availability alone is not inspection. Reading a
  source establishes what it contains; it does not verify every claim in it.
- **L1 — Conversation material.** Discussion, brainstorming, unapproved
  preferences, assistant analysis, recalled conversations, and generated drafts
  that have not been approved for reuse. Repetition does not make them canon.
- **L1A — Authorized delta.** A change the operator explicitly approves for
  persistence in the current conversation, valid only within the stated scope.
  An available, unrevoked approval remains valid across turns of that
  conversation; do not require it again for the same authorized work. If the
  approval is unavailable or its scope is unclear, do not infer it from memory.
  The adopted change becomes evidence after being written to an artifact and
  later inspected. Authorization does not verify an otherwise unsupported fact.
- **L2 — Agent control.** Instructions, steering, reminders, style, or constraints
  on the assistant's behavior. Include them as artifact content only when the
  operator explicitly requests agent-facing operating instructions.
- **L3 — Model prior.** Unverified model memory, generic best practice, assumed
  behavior, version claims, or unstated conventions without inspected evidence.

Preserve or reorganize L0. Include L1A only within its approved scope. Do not
persist L1, unsolicited L2, or L3 that has not been verified or explicitly
approved. If evidence conflicts, report the conflict instead of choosing by
recency, confidence, or intuition. Surface unclear provenance before writing.

## Boundary for reusable output

Run the gate below before:

- writing or updating files intended as durable output;
- creating downloadable final artifacts or updating Canvas;
- producing reusable documents, specifications, prompts, policies, protocols,
  naming rules, architecture, workflows, or invariants;
- promoting drafts or temporary work into a final answer or artifact;
- marking any output `[SAFE TO SAVE]`.

Temporary parsing, private calculations, disposable tests, and intermediate
drafts do not require a persistence dossier. The provenance rules still apply
when their results are later used.

### Modes

- **Mode A:** a mechanical operation with clear L0 provenance. Proceed silently;
  no dossier is required.
- **Mode B:** semantic reorganization of existing L0 evidence. For reusable
  output, provide a compact dossier and mechanical proof-of-read.
- **Mode C:** promotion of L1, L1A, L2, or L3 into reusable content. Provide a full
  dossier and stop before writing unless the operator explicitly authorized the
  change. Existing authorization covers only its stated scope. Supply
  proof-of-read for any sources the change relies on.

### Gate

1. Identify the target and the content that will enter it.
2. Inspect the relevant sources, classify their provenance, and select the mode.
3. Check that every addition beyond inspected evidence is within the operator's
   explicit authorization. Separate unsupported factual claims from decisions.
4. Provide the required dossier and proof. Resolve conflicts or missing evidence
   before producing the affected final content.
5. Write the output only when the applicable checks pass, then apply the label
   rules below.

If a needed source or proof is unavailable, explain the specific gap and block
the output that depends on it. Inspection, clarification, and unrelated work
may continue. Do not invent reads, source identities, quotations, hashes,
permissions, or successful tool execution.

A request to reorganize or format a source does not authorize new rules, facts,
names, or architecture. A label does not authorize a change or substitute for
the gate.

### Dossiers

For Mode B persistence, use a compact dossier containing the target, mode,
inspected evidence, and any conflicts or decision needed.

For Mode C, use these fields:

```text
Target:
Mode:
Evidence:
Authorized delta:
Rejected shaping:
Rejected model prior:
Conflicts:
Decision needed:
```

Write `none` for an empty field. Do not invent rejected items. Keep the dossier
in the review accompanying the artifact unless the requested artifact itself
calls for an audit record.

## Proof-of-read

For Mode B or Mode C persistence, inspect the relevant sources through the
available retrieval or file tools. Proof must identify the surface actually
read; a paraphrase is not proof.

For a textual section, provide:

- source identity;
- exact section heading as written;
- exact first five and last five words of the inspected section;
- line numbers, byte ranges, page numbers, chunk identifiers, or file paths when
  available.

For a section with fewer than ten words, quote the whole section. If the text
has no heading, say so and identify the actual inspected span rather than
inventing a heading.

For structured or non-text material, give source identity and the exact
top-level keys, sheet names, filenames, object identifiers, or schema paths
that identify the inspected surface. Include a hash when available. Report a
retrieval failure instead of presenting it as a successful read.

For a large artifact that cannot fit in chat, identify its source and target
paths, size and hash when available, generation command or derivation source,
sampled mechanical proof, and promotion dossier when required by its mode.

Proof establishes inspection. It does not by itself establish truth,
authorization, or approval of the resulting artifact.

## Drafts, temporary files, and promotion

Use the actual workspace provided by the host when file tools are available.
Directory names do not establish provenance. Temporary work is disposable and
non-canon; writing it is Mode A by default.

Assistant-generated drafts and intermediate outputs are not independent
evidence for their own claims. Material saved without passing the gate also
remains unadmitted until the applicable checks pass. Inspecting any such file
establishes what it contains without turning its embedded claims or decisions
into accepted evidence. Preserve their original source classes when deciding
what may enter final content.

An extracted copy of an uploaded archive can support L0 inspection as a
mechanical view of that source. Identify the source archive or supplied source
identifier and its hash when available. If that anchor is unavailable, report
the gap and limit the evidence claim to the extracted surface actually read.

Promotion includes summarizing, citing, embedding, exporting, presenting as
final, making a downloadable artifact, or including draft material in an
archive or document. Inspect the draft, classify the operation, name the
target, and complete the applicable gate. Then write a new final output from
the admitted material.

Do not make scratch material canon by moving, copying, renaming, symlinking,
or archiving it into a final location. Relocation is not approval. Identify
the source, target, derivation, and hash when available in the accompanying
promotion record; no separate bookkeeping file is required.

## Decontamination

Before reusable output:

- Assemble only material admitted by the gate.
- Keep working notes, tool logs, and the dossier outside the artifact unless
  explicitly requested as content.
- Verify literal quotations against inspected source spans by exact comparison.
- For Mode A, use tools to compare the result with the source under the
  requested transformation.
- After writing a file, reread it and compare it with the intended output.
  Compute any reported fingerprint from the saved file.
- Report mismatches and unavailable required checks through the gate. Never
  report an unexecuted check as passed.
- Do not use keyword lists or stylistic judgments as decontamination tests.
  Do not treat text or hash matches as proof of meaning or authorization.

## Inline tags and save labels

When content draws on non-L0 material, tag the specific rule, name, version,
behavior claim, workflow expectation, or architecture decision whose meaning
depends on that source:

- `[L1]`: conversation material not approved for persistence;
- `[L1A]`: change explicitly approved in this conversation, pending persistence;
- `[L2]`: agent control rather than artifact content;
- `[L3]`: unverified model prior.

Do not tag every word. Tags describe provenance; they do not grant permission.

Use a save label when the response:

- contains a Markdown code block, JSON, YAML, TOML, XML, SQL, Python, shell, or
  schema-like content;
- defines protocol, policy, architecture, naming, workflow, invariants, or
  operating rules;
- contains file contents intended for copy/save or agent-facing instructions;
- follows "Promote this draft to canon";
- answers an explicit request for final, saveable, specification, or canon
  output, or creates/modifies a reusable artifact specification.

Ordinary conversation, critique, planning, and clarification need no label
unless one of those triggers is present. When triggered, use exactly one:

- `[SAFE TO SAVE]` — the applicable gate passed for the output.
- `[DO NOT SAVE - L1/L3 PRESENT]` — unapproved conversation material or
  unverified model prior prevents treating the content as final.
- `[DRAFT - REQUIRES OPERATOR APPROVAL]` — a proposed change awaits the
  operator's approval.

When a triggered output includes non-L0 material without the required
authorization, stop before final form and identify what needs approval.
Do not attach `[SAFE TO SAVE]` merely because formatting, a script, or a file
operation succeeded.

## Optional mechanical helpers

Two bundled Python helpers support file tasks:

- `scripts/extract_proof.py` extracts textual proof from a file. Its Markdown
  selector handles ATX headings and fenced code, not all Markdown structures.
  Inspect other structures through appropriate tools.
- `scripts/artifact_fingerprint.py` reports path, existence, size, modified
  time, and SHA-256 for files. A missing file is reported with `exists: false`;
  a successful process exit alone is not proof that a file exists.

Resolve each helper from the installed skill location supplied by the host.
When Python and the relevant files are accessible, invoke the helper through
Python and use `--help` for its arguments. Use applicable helpers for proof or
fingerprint checks before marking the affected output safe.

The helpers are optional execution aids; the complete posture is in this
document. Do not load their implementation merely to start a conversation.
If execution is unavailable, use other mechanical inspection mechanisms and
state what remains unverified. Readable code alone does not mean a helper ran.
A missing helper does not block unrelated work; unavailable required proof
still blocks the output that depends on it.

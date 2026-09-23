# Canon Boundary Guard — ChatGPT plugin

A personal documentary plugin by **XxYouDeaDPunKxX**.
Version: **0.3.2**.

Canon Boundary Guard applies a provenance posture throughout a ChatGPT
conversation. It separates inspected evidence, discussion, explicitly authorized
changes, instructions to the assistant, and unverified assumptions before they
enter reusable answers or artifacts.

## Personal import

From the repository root, build with `python tools/package_plugin.py`.
In ChatGPT web, open the plugin creation dialog from the Plugins page, upload
`dist/canon-boundary-guard-0.3.2.zip`, and complete the add-plugin flow.
Use the generated plugin archive rather than a ZIP of the repository.

Activate Canon Boundary Guard through your ChatGPT custom instructions or
explicitly select/tag the plugin in the first message of a new conversation.
For custom instructions, use:

> Use Canon Boundary Guard from the start of every conversation. Read its complete
> skill before the first substantive response and apply it throughout the chat.

Once loaded, the complete posture applies before the first substantive response
and remains active throughout the chat. No initialization declaration or
working file is required.

The skill metadata targets `CHAT` and permits implicit invocation. The
description is not an executable session-start hook: installation alone does
not establish that the skill was loaded. Activation through custom instructions
or an explicit tag is the supported setup here.

## Operating scope

The complete rules are in
[SKILL.md](skills/canon-boundary-guard/SKILL.md). Ordinary conversation needs no
status announcement. Reusable content receives the applicable provenance,
authorization, proof, and label checks.

Explicit approval remains valid within its scope across turns of the current
conversation. The plugin does not carry decisions between conversations.
Previously supplied material is assessed through its actual contents and
available authorization; there is no automatic continuity or recovery process.

Missing evidence blocks the output that depends on it. It does not disable
unrelated work. A generated draft or an unchecked saved artifact does not become
evidence for its own claims merely because it is read again.

## Included files

```text
canon-boundary-guard/
  plugin.json
  LICENSE
  README.md
  skills/canon-boundary-guard/
    SKILL.md
    agents/openai.yaml
    scripts/
      extract_proof.py
      artifact_fingerprint.py
```

The optional helpers extract textual proof and compute file fingerprints.
They use Python's standard library. Python and accessible files are needed to
execute them; the posture also supports other mechanical inspection tools.
Their implementation need not be read during ordinary conversation.
For a file with no text lines, the proof helper reports `line_range: null`,
zero words and empty word lists. Its text output says `none (empty file)`.

## Verification

The repository tests cover packaging, resource references, unchanged helper
copies, archive contents, and execution of extracted helpers from another
working directory. Run `python -B -X utf8 tools/verify_plugin.py` from the
repository root to generate local test logs and package results in `dist/`.
These checks do not establish ChatGPT's loading or instruction-following behavior.

To verify the installed plugin, activate it in a new ChatGPT web conversation
through custom instructions or an explicit tag. Check that the complete skill
is read before substantive output, then exercise source-based reusable output,
an authorized change, an unapproved addition, and unavailable evidence. A claim
that the skill is active is not evidence that the required reads or checks ran.

## Attribution

Adapted from [Canon Boundary Guard](https://github.com/xxyoudeadpunkxx/canon-boundary-guard-for-gpt-project)
by **XxYouDeaDPunKxX**, under **CC BY-SA 4.0**. The [license](LICENSE) is included.

Changes dated September 23, 2026: conversation-scoped operation, consolidated
instructions, removal of continuity bookkeeping and its implementation,
retained proof/hash helpers, and mechanical output checks replacing linguistic
decontamination heuristics. The original source distribution remains
separate in the repository.

Version 0.3.2 corrects the proof helper's empty-file range. Posture instructions
and authorization rules are unchanged.

Format references: [plugin packaging](https://developers.openai.com/plugins/build/plugins),
[skill loading](https://developers.openai.com/plugins/concepts/skills),
and [package validation](https://developers.openai.com/plugins/deploy/submission-errors).

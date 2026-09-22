# Proof of Read

For Mode B or Mode C persistence, inspect relevant sources through available retrieval/file mechanisms.

Do not hardcode a tool name.

Proof-of-read must be mechanical.

## Textual source section

Provide:
- source identity
- exact section heading as written
- exact first 5 words of the inspected section
- exact last 5 words of the inspected section
- line numbers, byte ranges, page numbers, chunk identifiers, or file paths if available

If the section has fewer than 10 words, quote the entire section.

A paraphrase alone is never proof-of-read.

## Structured or non-text source

Provide:
- source identity
- exact top-level keys, sheet names, filenames, object identifiers, or schema paths
- hash if available
- retrieval failure if unavailable

## Failure

If proof-of-read is unavailable:
- treat the source as unavailable
- block persistence
- enter read-only mode for the target if necessary

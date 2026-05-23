# Scratch and Canon

## Runtime layout

`/mnt/data/scratch/**`
- disposable workspace
- non-canon
- Mode A by default

`/mnt/data/canon/**`
- guarded candidate outputs
- requires gate before creation or update

`/mnt/data/_SESSION_STATE.json`
- working state only

## Scratch zone

Scratch files are not evidence.

Exception:
A source-staged extraction of an uploaded or Project Source zip may support L0
inspection only as a mechanical view of that source, anchored to source identity
or hash. This exception applies to the inspected source surface only.
Assistant-generated scratch outputs remain non-evidence.

Before treating an extracted surface as L0, record the source zip path or source
id and hash if available. If source identity or hash is unavailable, declare the
missing anchor and limit L0 to the inspected extracted path with a risk note.

Allowed scratch uses:
- temporary extraction
- parsing
- calculations
- tests
- drafts
- intermediate transforms
- staging files before inspection

## Promotion boundary

Any movement from scratch to canon requires gate classification.

Promotion includes:
- copying
- summarizing
- exporting
- citing
- embedding
- presenting as final
- saving as downloadable artifact
- saving as Project Source
- including in an archive
- rendering into Canvas or final document

Rules:
- scratch -> scratch: free
- scratch -> canon: gate
- scratch -> response intended for save: gate
- scratch -> Project Source: gate

## Forbidden direct promotions

The assistant must not move, copy, rename, symlink, archive, or export files from `/mnt/data/scratch/**` to `/mnt/data/canon/**` or final artifact paths through direct filesystem operations.

Forbidden examples:
- os.rename
- shutil.move
- shutil.copy
- cp
- mv
- rsync
- zip/tar creation that includes scratch files as final outputs
- script that bulk-copies scratch outputs into canon without gate metadata

## Allowed promotion path

1. Inspect the scratch source.
2. Classify the promotion as Mode A, Mode B, or Mode C.
3. Produce required dossier if Mode B or Mode C.
4. Declare target path.
5. Write a new output file to `/mnt/data/canon/**` or final destination after gate approval.
6. Record source path, target path, content hash if available, and promotion reason in SESSION_STATE / CANON_STATE_DELTA.

For large files that cannot fit in chat, provide:
- source path
- target path
- size
- hash if available
- generation command or derivation source
- sampled mechanical proof
- promotion dossier

Invariant:
No scratch artifact becomes canon by relocation.
Canon artifacts are newly written after gate approval.

# Character Knowledge Workflow

This document describes the current character-knowledge workflow, the intended
system boundaries, and the near-term TODO list for the Novelist project.

The current implementation is intentionally optimized for the demo scope:

- generate one volume at a time
- keep character modeling sparse by default
- keep post-generation character updates conservative
- avoid hard-coding full narrative-function logic into character canon

## Scope

The character subsystem is responsible for:

- importing existing canonical character knowledge
- optionally reading volume-scoped preparation input
- discovering characters from generated text
- resolving discovered candidates against known canon
- applying conservative updates for recurring characters
- exporting a machine-readable knowledge snapshot and review reports

The subsystem is not yet responsible for:

- relationship graph persistence
- scene/plot-level character resolution
- narrative-function modeling
- human review / edit UI
- world-memory or faction-memory updates

## Current Inputs

The current run can consume these files:

- `input/input.txt`
  The main story requirement prompt.
- `input/knowledge/characters.json`
  Optional imported canonical character knowledge from previous work.
- `input/volume_preparation.json`
  Optional volume-scoped preparation input that tells the workflow which
  important characters are expected for the current run.

`volume_preparation.json` is intentionally a lightweight planning hint, not a
strict whitelist.

## Current Outputs

After a run, the workflow writes:

- `intermediate/knowledge/characters.json`
  Canonical character snapshot after create/update work.
- `intermediate/knowledge/ambiguous_resolutions.json`
  Resolver outputs that were too uncertain to auto-apply.
- `intermediate/knowledge/discovered_candidates.json`
  New character candidates that were created during the run.

The CLI also prints a short summary with counts for:

- imported characters
- created characters
- updated characters
- ambiguous resolutions
- preparation warnings

## High-Level Workflow

The current flow is:

1. `NovelGenerator` produces novel text from `input/input.txt`.
2. `CharacterKnowledgeWorkflow` loads imported canonical characters from
   `input/knowledge/characters.json` when present.
3. `CharacterKnowledgeWorkflow` loads `input/volume_preparation.json` when
   present.
4. The discovery extractor converts raw text into sparse `CharacterCandidate`
   objects.
5. The resolver tries to match each candidate to:
   - the prepared character shortlist first
   - the full imported character set second
6. The workflow applies one of three decisions:
   - `CREATE`: create a new canonical character
   - `UPDATE`: produce and apply a conservative patch
   - `AMBIGUOUS`: record the uncertainty and do not guess
7. The workflow exports the updated snapshot and review reports under
   `intermediate/knowledge/`.

## Why Volume Preparation Exists

Pure post-generation resolution is inherently ambiguous once a project grows.
Names, titles, aliases, and epithets can easily overlap.

`input/volume_preparation.json` reduces that ambiguity by giving the workflow a
strong prior over the important cast for the current run.

Example use cases:

- the author knows the lead and major recurring characters for this volume
- the author wants the resolver to prefer one known `Edric` over another
- the author wants the LLM to be free to create supporting/minor characters,
  but still anchor the major cast

If the file does not exist, the current default is:

- the LLM and extractor infer the working cast from the generated text
- the resolver falls back to the imported knowledge base only

## Design Principles

### 1. Canonical character data stays separate from narrative analysis

`Character` stores continuity-worthy person data:

- canonical name and aliases
- short retrieval summary
- stable tendencies
- optional profile modules

It does not store:

- protagonist arc logic
- theme-role annotations
- scene-local mood/state

### 2. Summary-first, detail-later

Most characters should stay cheap.

The default project strategy is:

- `core` profiles for many characters
- richer modules only when the text explicitly supports them

### 3. Conservative recurring updates

The updater is intentionally conservative:

- it appends durable aliases/tendencies
- it carries optional modules only when policy allows them
- it avoids rewriting the full profile from a single chapter or pass

### 4. Human input is advisory but valuable

`volume_preparation.json` is a strong prior, not a hard ban list.

That means:

- listed characters are preferred during resolution
- unlisted characters may still be discovered and created
- unresolved preparation entries become warnings, not hard failures

### 5. Ambiguity should be visible

Before an IDE exists, the system should not silently swallow uncertainty.

That is why ambiguous results are written to:

- `intermediate/knowledge/ambiguous_resolutions.json`

## Core Components

### `src/characters/models.py`

Defines canonical data models:

- `Character`
- `CharacterCandidate`
- `CharacterUpdateCandidate`
- `CharacterResolution`
- `VolumePreparation`
- optional profile modules

### `src/characters/extractor.py`

Discovery-oriented extraction only.

Responsibilities:

- read text
- produce sparse `CharacterCandidate` objects
- stay conservative about optional modules

Non-responsibilities:

- storage
- merge policy
- relationship persistence

### `src/characters/resolver.py`

Identity-matching logic.

Responsibilities:

- decide `CREATE`, `UPDATE`, or `AMBIGUOUS`

Current strategy:

- deterministic name/alias matching
- conservative on uncertainty

### `src/characters/updater.py`

Recurring-character patch extraction.

Responsibilities:

- convert a matched candidate into a sparse update proposal

### `src/characters/service.py`

Canonical business rules.

Responsibilities:

- validation
- normalization
- duplicate detection
- create/update/merge behavior
- imported-knowledge validation

### `src/characters/knowledge.py`

JSON import/export helpers.

Responsibilities:

- read and write character snapshots
- read volume preparation input
- write ambiguity and discovery reports

### `src/characters/workflow.py`

Orchestration layer.

Responsibilities:

- load inputs
- run extractor/resolver/updater in order
- apply canonical changes
- emit outputs

## Current Limitations

These are known limitations in the current demo-oriented design:

- the resolver is still surface-form based, not plot-aware
- volume preparation only influences resolution after text generation
- no relationship graph exists yet
- no review UI exists; all non-ambiguous proposals auto-apply
- no world-memory update path exists yet
- no character-memory/history model exists yet

## Why We Are Not Solving More Right Now

A full fix for cross-volume character identity would require workflow changes
above the character layer:

- plot objects carrying explicit character IDs
- scene/beat planning carrying resolved participants
- earlier resolution before prose generation
- possibly more structured orchestration than the current linear pipeline

That is real future work, but it is not the current project priority.

For the demo, the current tradeoff is:

- keep the main novel generation flow simple
- improve visibility and reduce silent errors
- avoid overbuilding before the IDE and planning workflow exist

## Recommended `volume_preparation.json` Shape

Minimal shape:

```json
{
  "known_characters": [
    {
      "character_id": "char_lyra",
      "canonical_name": "Lyra Vey",
      "aliases": ["Lady Vey"],
      "protagonist": true,
      "viewpoint": true,
      "volume_salience": "lead"
    }
  ]
}
```

Notes:

- `character_id` is preferred when known
- `canonical_name` and `aliases` help when the ID is absent
- `protagonist`, `viewpoint`, and `volume_salience` are scoped to this volume
- the file is optional

## Priority TODO

### P0

- keep ambiguity visible in CLI and JSON outputs
- keep `volume_preparation.json` optional and advisory
- keep imported knowledge validated through the service layer

### P1

- improve resolver behavior using `volume_preparation` metadata more explicitly
- track whether a created character came from preparation, imported canon, or
  pure discovery
- add tests for malformed `volume_preparation.json`
- add tests for ambiguous-resolution reporting

### P2

- add relationship-candidate extraction as a separate output stream
- add entity-kind support for non-human important characters
- support more explicit volume preparation policy for generated supporting/minor
  characters

### P3

- add reviewable proposal objects instead of auto-applying everything
- add change logs for accepted/rejected updates
- add IDE-facing inspection/edit workflow

### Later

- move character identity resolution earlier into plot / episode / scene stages
- add relationship graph persistence
- add character memory / world memory modules
- add narrative-function modeling as a separate layer

## Practical Guidance

For the current demo, the intended usage is:

1. put the novel requirement in `input/input.txt`
2. optionally import previous canon in `input/knowledge/characters.json`
3. optionally add important volume-specific character hints in
   `input/volume_preparation.json`
4. run the generator
5. inspect:
   - `intermediate/knowledge/characters.json`
   - `intermediate/knowledge/ambiguous_resolutions.json`
   - `intermediate/knowledge/discovered_candidates.json`

That is the current stable operating model until the project grows into a
heavier planning and review workflow.

# dontfeartheripper

A tool for cleaning up large FLAC music collections.

Over years of ripping CDs with tools such as Exact Audio Copy (EAC), CUERipper, Whipper and others, music libraries tend to accumulate inconsistencies:

- cryptic directory names
- incomplete metadata
- broken compilation tags
- missing artist information
- duplicate naming conventions
- mixed metadata quality

dontfeartheripper helps identify and repair these issues while keeping every change reviewable and reversible.

---

## What Problem Does It Solve?

Consider a library containing folders such as:

    VOR4RQ~J
    VECENK~E
    VHVOJJ~K

or albums with metadata like:

    Artist: Unknown Artist
    Album: Rage of the Hedgehog

or compilations where album metadata contains:

    VARIOUS

instead of:

    Various Artists

dontfeartheripper analyzes the collection, identifies problems, suggests repairs and can automatically fix a number of common metadata issues.

---

## Features

### Library Analysis

Inspect albums, compilations and soundtracks:

    dftr scan /music

Export results as JSON:

    dftr scan /music --json

### Diagnostics

Detect cryptic directory names, metadata issues and problematic library structures:

    dftr doctor /music

JSON output:

    dftr doctor /music --json

### Statistics

Generate library statistics:

    dftr stats /music

JSON output:

    dftr stats /music --json

### Quality Analysis

Evaluate metadata quality across the library:

    dftr quality /music

Example:

    Quality Score: 86%

    WARN album/foo
      missing_artist

    WARN compilation/bar
      inconsistent_artist_naming

JSON output:

    dftr quality /music --json

### Metadata Repair

Preview metadata repairs:

    dftr repair /music

Apply repairs:

    dftr repair /music --yes

Undo metadata repairs:

    dftr repair-undo

### Directory Renaming

Preview rename operations:

    dftr fix /music

Execute rename operations:

    dftr fix /music --yes

Undo the last rename batch:

    dftr undo

---

## Typical Workflow

Analyze the collection:

    dftr doctor /music
    dftr quality /music

Preview metadata repairs:

    dftr repair /music

Apply repairs:

    dftr repair /music --yes

Verify quality:

    dftr quality /music

Preview directory renames:

    dftr fix /music

Apply renames:

    dftr fix /music --yes

---

## Repair Rules

Current automatic repairs include:

### Missing Artist Detection

Before:

    Artist: Unknown Artist
    Folder: Loyft - Rage of the Hedgehog

After:

    Artist: Loyft

### Compilation Artist Normalization

Before:

    VARIOUS

After:

    Various Artists

Repairs operate directly on FLAC metadata and support rollback.

---

## JSON API

Machine-readable output is available for:

    dftr scan --json
    dftr doctor --json
    dftr stats --json
    dftr quality --json
    dftr repair --json

All JSON outputs include a schema version:

    {
      "schema_version": 1
    }

allowing future schema evolution without breaking integrations.

---

## Safety

dontfeartheripper is designed around safe workflows.

- Dry-run by default
- Explicit --yes required for modifications
- Rename rollback support
- Metadata repair rollback support
- Collision detection
- Container directory protection

Nothing is modified unless explicitly requested.

---

## Running Tests

    uv run pytest -v

Current test coverage includes:

- metadata repair planning
- repair safety checks
- quality scoring
- metadata source prioritization
- repair rule validation

---

## Requirements

- Python 3.14+
- FLAC-based music collection
- Metadata created by tools such as EAC, CUERipper, Whipper or similar

---

## License

GPL-3.0

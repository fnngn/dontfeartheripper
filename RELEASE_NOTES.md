# dontfeartheripper v0.1.2

## Highlights

Recursive album discovery is now supported across the entire library.

Albums are no longer limited to the first directory level below:

- album
- compilation
- soundtrack

This significantly improves support for nested collections, soundtrack archives and artist containers.

---

## New Features

### Recursive Album Discovery

Album directories are now discovered recursively.

Example:

    album/
    └── Truckfighters/
        ├── Gravity X
        ├── Mania
        ├── Phi
        └── Fuzzsplit of the Century

All albums are detected automatically.

---

### Expanded Audio Format Detection

Recursive detection now supports:

- FLAC
- MP3
- M4A
- AAC
- OGG
- OPUS
- WAV
- APE
- WV

---

### Improved Cover Discovery

Recursive scanning automatically expands cover detection and downloading.

Additional cover artwork successfully discovered:

- Gravity X
- Mania
- Phi
- Fuzzsplit of the Century
- Frostpunk Original Soundtrack

---

## Existing Features

### Library Analysis

    dftr scan

### Diagnostics

    dftr doctor

### Statistics

    dftr stats

### Quality Analysis

    dftr quality

### Metadata Repair

    dftr repair
    dftr repair --yes
    dftr repair-undo

### Directory Renaming

    dftr fix
    dftr fix --yes
    dftr undo

### Cover Art Management

    dftr cover
    dftr cover --fetch
    dftr cover --plan
    dftr cover --yes

---

## Test Status

    19 passed
    0 failed

# dontfeartheripper

Music library auditing, repair, artwork management and container discovery for large self-hosted collections.

dontfeartheripper is designed for music libraries that have grown over many years through:

- Exact Audio Copy (EAC)
- CUERipper
- Whipper
- Bandcamp downloads
- soundtrack archives
- discographies
- multi-disc releases

The goal is simple:

- discover problems
- repair metadata
- standardize artwork
- generate collection metadata
- prepare libraries for Jellyfin
- keep operations reversible

---

## Installation

### Requirements

- Python 3.14+
- uv

Install uv:

    curl -LsSf https://astral.sh/uv/install.sh | sh

Verify:

    uv --version

### Install from Source

Clone the repository:

    git clone https://github.com/fnngn/dontfeartheripper.git

Enter the project directory:

    cd dontfeartheripper

Install:

    uv tool install . --force

Verify:

    dftr --help

### Updating

Update repository:

    git pull

Reinstall:

    uv tool install . --force

### Development

Install development environment:

    uv sync

Run tests:

    uv run pytest -v

---

## Supported Audio Formats

Recursive album discovery supports:

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

## Features

### Library Analysis

Scan music libraries.

    dftr scan /music

JSON output:

    dftr scan /music --json

Detects:

- albums
- compilations
- soundtracks
- metadata sources
- disc numbers
- cryptic names
- rename candidates

---

### Diagnostics

Inspect library structure.

    dftr doctor /music

JSON output:

    dftr doctor /music --json

Detects:

- cryptic directory names
- rename collisions
- suspicious structures
- container directories

---

### Statistics

Generate collection statistics.

    dftr stats /music

JSON output:

    dftr stats /music --json

Includes:

- album count
- compilation count
- soundtrack count
- TOC usage
- CUE usage
- rename candidates
- collisions

---

### Quality Analysis

Evaluate metadata quality.

    dftr quality /music

JSON output:

    dftr quality /music --json

Current checks:

- missing artists
- missing albums
- weak metadata sources
- inconsistent compilation metadata
- container-related issues

---

### Metadata Repair

Preview:

    dftr repair /music

Apply:

    dftr repair /music --yes

Rollback:

    dftr repair-undo

Current repair rules:

- missing_artist
- various_uppercase
- various_mixed

Repairs are written directly into file metadata.

---

### Directory Renaming

Preview:

    dftr fix /music

Apply:

    dftr fix /music --yes

Rollback:

    dftr undo

---

## Cover Art Management

### Find Missing Artwork

    dftr cover /music

### Search Sources

    dftr cover /music --fetch

Sources:

- MusicBrainz
- Cover Art Archive

### Preview Downloads

    dftr cover /music --plan

### Download Artwork

    dftr cover /music --yes

### Artwork Policy

Recognized filenames:

    cover.*
    folder.*
    front.*
    artwork.*
    albumart.*

Supported image formats:

    jpg
    jpeg
    png

Recursive artwork discovery is supported.

Downloaded artwork is normalized to:

    cover.jpg

Compatible with:

- Jellyfin
- Plex
- Kodi
- Navidrome

---

## Container Engine

Version 0.1.3 introduces recursive container discovery.

Supported scenarios:

- artist discographies
- soundtrack collections
- multi-disc releases
- edition collections
- nested container structures

### Detect Containers

Preview:

    dftr container /music

Generate metadata:

    dftr container /music --yes

### Container Types

- artist_container
- disc_container
- edition_container
- soundtrack_container
- generic_container

### Generated Files

Container processing generates:

    .dftr-container.json
    collection.nfo
    poster.jpg

### Container Metadata

Generated metadata includes:

- container_id
- parent_container
- container_type
- album_count
- container_depth
- schema_version
- generated_by
- generated_version

Example:

    Truckfighters
    ├── .dftr-container.json
    ├── collection.nfo
    ├── poster.jpg
    ├── Gravity X
    ├── Mania
    ├── Phi
    └── Fuzzsplit of the Century

---

## Jellyfin Collection Foundation

Container generation creates:

    collection.nfo

Fields:

- title
- uniqueid
- overview
- type
- albumcount
- depth
- dateadded

Container artwork:

    poster.jpg

is generated automatically from existing child album artwork.

---

## Typical Workflow

Inspect:

    dftr doctor /music

Evaluate quality:

    dftr quality /music

Repair metadata:

    dftr repair /music --yes

Download cover art:

    dftr cover /music --yes

Generate collection metadata:

    dftr container /music --yes

Preview renames:

    dftr fix /music

Apply renames:

    dftr fix /music --yes

---

## JSON Output

Available for:

    dftr scan --json
    dftr doctor --json
    dftr stats --json
    dftr quality --json
    dftr repair --json
    dftr cover --fetch --json
    dftr cover --plan --json

All outputs include:

    {
      "schema_version": 1
    }

---

## Safety

dontfeartheripper follows a dry-run-first workflow.

Features:

- dry-run by default
- explicit --yes required
- metadata repair rollback
- rename rollback
- collision protection
- download planning
- container-aware processing

No modifications are performed unless explicitly requested.

---

## Testing

Run:

    uv run pytest -v

Current status:

    31 tests passing

---

## License

GPL-3.0

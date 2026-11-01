# dontfeartheripper

Music library auditing, repair, artwork management and container discovery for large self-hosted collections.

dontfeartheripper is designed for music collections that have grown over many years through:

- Exact Audio Copy (EAC)
- CUERipper
- Whipper
- Bandcamp downloads
- soundtrack archives
- artist discographies
- multi-disc releases

The project focuses on four areas:

- library analysis
- metadata repair
- artwork management
- collection and container management

All operations follow a dry-run-first workflow and are designed to be reversible whenever possible.

---

## Installation

### Requirements

- Python 3.14+
- uv

Verify uv:

    uv --version

### Install

Clone the repository:

    git clone https://github.com/fnngn/dontfeartheripper.git

Enter the project directory:

    cd dontfeartheripper

Run the installer:

    ./install.sh

Verify installation:

    dftr --help

### Update

Update repository:

    git pull

Reinstall:

    ./install.sh

### Development Environment

Install dependencies:

    uv sync

Run tests:

    uv run pytest -v

---

## Supported Audio Formats

Recursive album detection supports:

- FLAC
- MP3
- M4A
- AAC
- OGG
- OPUS
- WAV
- APE
- WV

Album discovery is recursive and no longer limited to a single directory level.

---

## Library Analysis

Scan a library:

    dftr scan /music

JSON output:

    dftr scan /music --json

Provides:

- album detection
- compilation detection
- soundtrack detection
- metadata source information
- track counts
- disc numbers
- container information
- rename candidates

---

## Diagnostics

Inspect library structure:

    dftr doctor /music

JSON output:

    dftr doctor /music --json

Detects:

- cryptic directory names
- rename collisions
- suspicious structures
- container directories

---

## Statistics

Generate statistics:

    dftr stats /music

JSON output:

    dftr stats /music --json

Includes:

- albums
- compilations
- soundtracks
- containers
- cryptic directories
- TOC usage
- CUE usage
- rename candidates
- collisions

---

## Quality Analysis

Evaluate metadata quality:

    dftr quality /music

JSON output:

    dftr quality /music --json

Current quality checks:

- missing artists
- missing album names
- weak metadata sources
- inconsistent compilation naming
- container metadata issues

Example:

    Quality Score: 86%

    WARN album/foo
      missing_artist

---

## Metadata Repair

Preview repairs:

    dftr repair /music

Apply repairs:

    dftr repair /music --yes

Rollback:

    dftr repair-undo

Current repair rules:

- missing_artist
- various_uppercase
- various_mixed

Repairs are written directly into file metadata.

Example:

Before:

    Artist: Unknown Artist

After:

    Artist: Loyft

---

## Directory Renaming

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

### Search Artwork Sources

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

Recognized formats:

    jpg
    jpeg
    png

Artwork discovery is recursive.

Downloaded artwork is always normalized to:

    cover.jpg

Compatible with:

- Jellyfin
- Plex
- Kodi
- Navidrome

---

## Container Engine

Version 0.1.3 introduces a dedicated container engine.

The container engine models structures such as:

### Artist Containers

Example:

    Truckfighters
    ├── Gravity X
    ├── Mania
    ├── Phi
    └── Fuzzsplit of the Century

### Disc Containers

Example:

    Album
    ├── CD1
    ├── CD2
    └── CD3

### Edition Containers

Example:

    Frostpunk Original Soundtrack
    ├── FLAC
    └── WAV

### Soundtrack Containers

Example:

    Cyberpunk 2077 Bonus Content
    └── soundtrack
        └── mp3

### Detect Containers

Preview:

    dftr container /music

Generate metadata:

    dftr container /music --yes

### Supported Container Types

- artist_container
- disc_container
- edition_container
- soundtrack_container
- generic_container

### Generated Files

Container processing creates:

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

Container processing generates:

    collection.nfo

Current metadata fields:

- title
- uniqueid
- overview
- type
- albumcount
- depth
- dateadded

Container artwork:

    poster.jpg

is automatically derived from existing child album artwork.

This provides the foundation for Jellyfin collection support.

---

## Typical Workflow

Inspect:

    dftr doctor /music

Evaluate quality:

    dftr quality /music

Repair metadata:

    dftr repair /music --yes

Download artwork:

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

All formats include:

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
- recursive discovery
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

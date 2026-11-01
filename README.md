# dontfeartheripper

Music library auditing, metadata recovery, artwork management and container discovery for large self-hosted music collections.

dontfeartheripper is designed for archives that have grown over many years through:

- Exact Audio Copy (EAC)
- CUERipper
- Whipper
- Bandcamp downloads
- soundtrack archives
- artist discographies
- multi-disc releases

The project focuses on:

- library analysis
- metadata repair
- cover management
- container discovery
- collection metadata generation
- Jellyfin preparation

---

## Installation

### Requirements

- Python 3.14+
- uv

### Install

Clone:

    git clone https://github.com/fnngn/dontfeartheripper.git

Enter repository:

    cd dontfeartheripper

Install:

    ./install.sh

Verify:

    dftr --help

### Update

    git pull
    ./install.sh

### Development

Install dependencies:

    uv sync

Run tests:

    uv run pytest -v

---

## Supported Audio Formats

Recursive discovery supports:

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

## Commands

### Scan Library

    dftr scan /music

JSON:

    dftr scan /music --json

---

### Diagnostics

    dftr doctor /music

JSON:

    dftr doctor /music --json

---

### Statistics

    dftr stats /music

JSON:

    dftr stats /music --json

---

### Quality Analysis

    dftr quality /music

JSON:

    dftr quality /music --json

Checks:

- missing artists
- missing albums
- weak metadata sources
- inconsistent compilation metadata
- container metadata issues

---

### Metadata Repair

Preview:

    dftr repair /music

Apply:

    dftr repair /music --yes

Undo:

    dftr repair-undo

Current repair rules:

- missing_artist
- various_uppercase
- various_mixed
- recovery candidate generation

---

### Directory Renaming

Preview:

    dftr fix /music

Apply:

    dftr fix /music --yes

Undo:

    dftr undo

---

## Cover Art Management

Find missing artwork:

    dftr cover /music

Lookup candidates:

    dftr cover /music --fetch

Preview downloads:

    dftr cover /music --plan

Download artwork:

    dftr cover /music --yes

Sources:

- MusicBrainz
- Cover Art Archive

Recognized filenames:

    cover.*
    folder.*
    front.*
    artwork.*
    albumart.*

Downloaded artwork is normalized to:

    cover.jpg

Compatible with:

- Jellyfin
- Plex
- Kodi
- Navidrome

---

## Container Engine

Detect containers:

    dftr container /music

Generate metadata:

    dftr container /music --yes

Supported container types:

- artist_container
- disc_container
- edition_container
- soundtrack_container
- generic_container

Generated files:

    .dftr-container.json
    collection.nfo
    poster.jpg

Metadata fields:

- container_id
- parent_container
- container_type
- album_count
- container_depth
- schema_version
- generated_version

Examples:

- artist discographies
- soundtrack collections
- edition collections
- multi-disc releases

---

## Metadata Recovery Engine

The metadata recovery engine is container-aware.

Recovery priority:

1. local metadata
2. container metadata
3. album.nfo
4. TOC/CUE
5. MusicBrainz

Local metadata always wins.

Core components:

- TrackMetadata
- Recovery Candidate Builder
- Recovery Operations
- Container Context Resolution

---

## Jellyfin Collection Foundation

Generated collection metadata:

    collection.nfo

contains:

- title
- uniqueid
- overview
- type
- albumcount
- depth
- dateadded

Generated artwork:

    poster.jpg

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

All outputs contain:

    {
      "schema_version": 1
    }

---

## Safety

dontfeartheripper follows a dry-run-first workflow.

Features:

- dry-run by default
- explicit --yes required
- rename rollback
- metadata rollback
- download planning
- collision protection
- recursive discovery

---

## Testing

Run:

    uv run pytest -v

Current status:

    46 tests passing

---

## License

GPL-3.0

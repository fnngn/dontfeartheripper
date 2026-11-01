# dontfeartheripper

Music library auditing, metadata recovery, artwork management and container discovery for large self-hosted music collections.

dontfeartheripper is designed for collections built from:

- Exact Audio Copy (EAC)
- CUERipper
- Whipper
- Bandcamp downloads
- soundtrack archives
- artist discographies
- multi-disc releases
- deluxe editions

The project focuses on:

- library analysis
- metadata repair
- metadata recovery
- artwork management
- container discovery
- collection metadata generation
- Jellyfin preparation

---

## Installation

### Requirements

- Python 3.14+
- uv

### Install

Clone repository:

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

Evaluates:

- metadata completeness
- metadata source quality
- container consistency
- naming consistency

---

### Metadata Repair

Preview:

    dftr repair /music

Apply:

    dftr repair /music --yes

Undo:

    dftr repair-undo

Supports:

- artist recovery
- albumartist recovery
- album recovery
- NFO recovery
- container-aware recovery

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

Recognized artwork:

- cover.*
- folder.*
- front.*
- artwork.*
- albumart.*

Normalized output:

    cover.jpg

Compatible with:

- Jellyfin
- Plex
- Kodi
- Navidrome

---

## Container Engine

Detect:

    dftr container /music

Generate metadata:

    dftr container /music --yes

Supported container types:

- artist_container
- disc_container
- format_container
- soundtrack_container
- generic_container

Examples:

### Artist Container

    Truckfighters
    ├── Gravity X
    ├── Mania
    ├── Phi
    └── Fuzzsplit of the Century

### Disc Container

    Tea For The Tillerman (Super Deluxe)
    ├── Disc 1
    ├── Disc 2
    ├── Disc 3
    └── Disc 4

### Format Container

    Frostpunk Original Soundtrack
    ├── FLAC
    └── WAV

Generated:

    .dftr-container.json
    collection.nfo
    poster.jpg

Metadata includes:

- container_id
- parent_container
- container_type
- album_count
- container_depth

---

## Metadata Recovery Engine

Recovery priority:

1. local metadata
2. album.nfo
3. container metadata
4. TOC/CUE
5. MusicBrainz

Local metadata always wins.

Core components:

- TrackMetadata
- Recovery Candidate Builder
- Recovery Operations
- Container Context Resolution
- nearest album.nfo lookup

Real-world examples:

- Cyberpunk 2077 → Marcin Przybylowicz
- Frostpunk → Piotr Musiał
- The Thaumaturge → Agnieszka Wlazly

---

## Jellyfin Collection Foundation

Generated metadata:

    collection.nfo

Generated artwork:

    poster.jpg

Provides a foundation for Jellyfin collection handling.

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

Features:

- dry-run by default
- explicit --yes required
- metadata rollback
- rename rollback
- collision protection
- container-aware processing

---

## Testing

Run:

    uv run pytest -v

Current status:

    54 tests passing

Quality example:

    Quality Score: 100%

---

## License

GPL-3.0

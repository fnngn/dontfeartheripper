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

### Terminal UI

Start the keyboard-driven library dashboard:

    dftr tui /music

Choose a section in the main menu with the arrow keys (or `j`/`k`) and press
Enter to open its options. Press Escape or Backspace to return to the main
menu. Scroll long reports with Page Up/Page Down, refresh the scan with `r`,
and quit with `q`. Changes to tags, directories, or container metadata require
a separate confirmation. The restrained playlist-style interface uses your
terminal's default colors and background. Scans and long-running actions run
in the background and show a live progress indicator and current operation.
Command-line scans, cover lookups, downloads, and Jellyfin operations also
show progress when run in an interactive terminal.
Choose **Library → Search library** to find songs, albums, artists, genres, and
local collections. Search is case-insensitive and checks audio tags as well as
file and collection names; track-tag searches run in the background.
During a TUI task, press `Esc` or `Ctrl-C` to stop at the next safe checkpoint.
In CLI commands, `Ctrl-C` requests the same cooperative stop. The current
network or file operation is allowed to finish; completed file changes remain
available through their undo logs, while completed Jellyfin changes should be
reviewed before retrying.

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

`--yes` looks up missing covers before downloading and does not overwrite
existing `cover.jpg` files.

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

The `container` command writes local DFTR metadata and artwork. `collection.nfo`
is not sufficient to create a native Jellyfin collection; use the Jellyfin
integration below to create collections on the server.

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
    poster.jpg (or poster.png when the source art is PNG)

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

## Jellyfin Collections

The integration creates and synchronizes native Jellyfin collections through
the Jellyfin API, adds the matching music albums, and uploads available album
art as the collection poster when no poster exists yet (existing posters are
preserved). It matches albums by their paths; use `--server-root` when the
path on Jellyfin differs from the local path. Nested disc folders are matched
to their Jellyfin album folder, so a multi-disc album is added only once.

Create an administrator API key in Jellyfin with collection-management
permissions, then provide it through the environment (the key is never written
to the library):

    export JELLYFIN_URL=http://jellyfin:8096
    export JELLYFIN_API_KEY=your-api-key

Optional: set the path prefix as seen by Jellyfin, relative to the supplied
local library root:

    export JELLYFIN_LIBRARY_ROOT=/music

Preview the match plan (the default; no collections are changed):

    dftr jellyfin-collections /mnt/music

Create or synchronize native collections:

    dftr jellyfin-collections /mnt/music --yes

The TUI provides **Jellyfin collection plan** and **Publish Jellyfin
collections** actions. The publishing action requires confirmation. Configure
the same environment variables before launching `dftr tui /mnt/music`.

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
    dftr jellyfin-collections /music --json

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

Current test suite:

    85 tests passing

Quality example:

    Quality Score: 100%

---

## License

GPL-3.0

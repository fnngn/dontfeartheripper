# dontfeartheripper

A small utility for cleaning up large FLAC collections that have been ripped over decades with tools like EAC, Whipper and CUERipper.

If your library contains directories like

    VOR4RQ~J
    VECENK~E
    VHVOJJ~K

instead of actual album names, this tool is for you.

## Quick Start

Inspect your library:

    dftr doctor /music

Preview rename operations:

    dftr fix /music

Execute rename operations:

    dftr fix /music --yes

By default, fix runs in dry-run mode and performs no changes.

## Quick Start

Inspect the library and look for problems:

    dftr doctor /music

Preview all planned rename operations:

    dftr fix /music

Execute the rename operations:

    dftr fix /music --yes

Undo the most recent rename operation:

    dftr undo

Typical workflow:

    dftr doctor /music
    dftr fix /music
    dftr fix /music --yes

If necessary:

    dftr undo

The fix command runs in dry-run mode by default.

No files or directories are modified unless --yes is specified.

The undo command restores the most recent successful rename operation using:

    .dftr-last-rename.json

## Features

- Detect cryptic directory names
- Parse TOC metadata
- Recover metadata from FLAC tags
- Read album.nfo files
- Detect multi-disc releases
- Generate rename suggestions
- Detect rename collisions
- Detect container/discography directories
- Rename cryptic album folders

## Metadata Sources

Priority order:

1. TOC
2. FLAC tags
3. album.nfo

Low quality metadata is automatically replaced by better information if available.

## Multi-Disc Releases

Disc 1 keeps the normal album title:

    Artist - Album

Additional discs receive a suffix:

    Artist - Album - CD 2
    Artist - Album - CD 3

Existing disc suffixes are preserved and never duplicated.

## Example

Before:

    compilation/
      VREKYT~E
      VSHYFY~X
      VKTVPF~G

After:

    compilation/
      Various Artists - Blues Giants - The Essential Songbook
      Various Artists - Blues Giants - The Essential Songbook - CD 2
      Various Artists - Blues Giants - The Essential Songbook - CD 3

## Installation

Requirements:

- Python 3.14+
- uv

Install:

    ./install.sh

## Commands

Scan:

    dftr scan /path/to/music

Diagnose:

    dftr doctor /path/to/music

Rename preview:

    dftr fix /path/to/music

Execute rename:

    dftr fix /path/to/music --yes

## Project Status

Version: 0.0.3

The project is already usable for real-world library cleanup but remains experimental.

Always keep backups before performing large renames.

## License

GNU General Public License v3.0 (GPL-3.0)

## Why?

Because life's too short to manually rename ten thousand FLAC albums.

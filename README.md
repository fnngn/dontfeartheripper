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

Generate statistics:

    dftr stats /music

Preview rename operations:

    dftr fix /music

Execute rename operations:

    dftr fix /music --yes

Undo the most recent rename operation:

    dftr undo

Typical workflow:

    dftr doctor /music
    dftr stats /music
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
- Detect container/discography directories
- Generate rename suggestions
- Detect rename collisions
- Perform automatic folder renames
- Undo the most recent rename operation
- Generate library statistics

## Commands

Scan metadata:

    dftr scan /path/to/music

Diagnose problems:

    dftr doctor /path/to/music

Show statistics:

    dftr stats /path/to/music

Preview rename operations:

    dftr fix /path/to/music

Execute rename operations:

    dftr fix /path/to/music --yes

Rollback previous rename:

    dftr undo

## Statistics

Example:

    Library Statistics

    Albums:             12345
    Compilations:         789
    Soundtracks:          123

    Containers:            54
    Cryptic:                0

    TOC files:          11000
    CUE files:          10998

    Rename candidates:     0
    Collisions:            0

## Metadata Sources

Priority order:

1. TOC
2. FLAC tags
3. album.nfo

## Multi-Disc Releases

Disc 1 keeps the normal album title:

    Artist - Album

Additional discs receive a suffix:

    Artist - Album - CD 2
    Artist - Album - CD 3

Existing disc suffixes are preserved and never duplicated.

## License

GNU General Public License v3.0 (GPL-3.0)

## Why?

Because life's too short to manually rename ten thousand FLAC albums.

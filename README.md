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

Generate JSON statistics:

    dftr stats /music --json

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
- Undo previous rename operations
- Generate library statistics
- Export statistics as JSON

## Commands

Scan metadata:

    dftr scan /path/to/music

Diagnose problems:

    dftr doctor /path/to/music

Human readable statistics:

    dftr stats /path/to/music

JSON statistics:

    dftr stats /path/to/music --json

Preview rename operations:

    dftr fix /path/to/music

Execute rename operations:

    dftr fix /path/to/music --yes

Rollback previous rename:

    dftr undo

## JSON Schema

Version 1:

{
  "schema_version": 1,
  "albums": 0,
  "compilations": 0,
  "soundtracks": 0,
  "containers": 0,
  "cryptic": 0,
  "toc_files": 0,
  "cue_files": 0,
  "rename_candidates": 0,
  "collisions": 0
}

Example:

    dftr stats /music --json | jq .

## License

GNU General Public License v3.0 (GPL-3.0)

## Why?

Because life's too short to manually rename ten thousand FLAC albums.

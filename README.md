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

Generate JSON diagnostics:

    dftr doctor /music --json

Generate statistics:

    dftr stats /music

Generate JSON statistics:

    dftr stats /music --json

Export complete library metadata:

    dftr scan /music --json

Preview rename operations:

    dftr fix /music

Execute rename operations:

    dftr fix /music --yes

Undo the most recent rename operation:

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
- Export scan results as JSON
- Export diagnostics as JSON
- Export statistics as JSON

## Commands

    dftr scan
    dftr scan --json

    dftr doctor
    dftr doctor --json

    dftr stats
    dftr stats --json

    dftr fix
    dftr fix --yes

    dftr undo

## JSON Support

The following commands support structured JSON output:

    dftr scan --json
    dftr doctor --json
    dftr stats --json

All JSON formats contain:

    "schema_version": 1

to support future schema evolution.

## Scan JSON Schema

{
  "schema_version": 1,
  "items": [
    {
      "path": "...",
      "category": "album",
      "artist": "...",
      "album": "...",
      "tracks": 0,
      "flacs": 0,
      "has_toc": false,
      "has_cue": false,
      "metadata_source": "unknown",
      "container": false,
      "cryptic": false,
      "rename_candidate": false,
      "suggested_name": null,
      "disc_number": null,
      "rename_collision": false
    }
  ]
}

## License

GNU General Public License v3.0 (GPL-3.0)

## Why?

Because life's too short to manually rename ten thousand FLAC albums.

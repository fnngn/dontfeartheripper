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

Generate machine readable diagnostics:

    dftr doctor /music --json

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
- Export diagnostics as JSON

## Commands

    dftr scan
    dftr doctor
    dftr doctor --json
    dftr stats
    dftr stats --json
    dftr fix
    dftr fix --yes
    dftr undo

## JSON Output

Statistics:

    dftr stats /music --json

Diagnostics:

    dftr doctor /music --json

Both JSON formats contain a schema_version field to support future extensions without breaking compatibility.

## License

GNU General Public License v3.0 (GPL-3.0)

## Why?

Because life's too short to manually rename ten thousand FLAC albums.

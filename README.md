# dontfeartheripper

A small utility for cleaning up large FLAC collections that have been ripped over decades with tools like EAC, Whipper and CUERipper.

## Quick Start

Inspect library:

    dftr doctor /music

Quality report:

    dftr quality /music

JSON quality report:

    dftr quality /music --json

Statistics:

    dftr stats /music

JSON statistics:

    dftr stats /music --json

Library export:

    dftr scan /music --json

Preview rename operations:

    dftr fix /music

Execute rename operations:

    dftr fix /music --yes

Rollback:

    dftr undo

## Commands

    dftr scan
    dftr scan --json

    dftr doctor
    dftr doctor --json

    dftr stats
    dftr stats --json

    dftr quality
    dftr quality --json

    dftr fix
    dftr fix --yes

    dftr undo

## Quality Analysis

Current rules:

- missing_artist
- missing_album
- unknown_metadata_source
- inconsistent_artist_naming
- container_has_metadata

Example:

    Quality Score: 86%

    WARN album/foo
      missing_artist

    WARN album/bar
      inconsistent_artist_naming

## JSON Support

    dftr scan --json
    dftr doctor --json
    dftr stats --json
    dftr quality --json

All JSON formats contain:

    schema_version

for future compatibility.

## License

GNU General Public License v3.0 (GPL-3.0)

## Why?

Because life's too short to manually rename ten thousand FLAC albums.

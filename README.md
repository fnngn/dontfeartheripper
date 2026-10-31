# dontfeartheripper

A small utility for cleaning up large FLAC collections that have been ripped over decades with tools like EAC, Whipper and CUERipper.

If your library contains directories like

    VOR4RQ~J
    VECENK~E
    VHVOJJ~K

instead of actual album names, this tool is for you.

## What it does

dontfeartheripper scans a music library and tries to recover meaningful album names from multiple metadata sources.

Supported sources:

- TOC files
- FLAC tags
- album.nfo files
- GNUdb lookups (experimental)

The tool can then generate safe rename suggestions and optionally rename cryptic album directories.

## Features

- Detect cryptic directory names
- Parse TOC metadata
- Recover metadata from FLAC tags
- Read album.nfo files
- Detect multi-disc releases
- Detect discography/container directories
- Generate rename suggestions
- Detect rename collisions
- Perform automatic folder renames

## Metadata Priority

Metadata quality varies wildly depending on the source.

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

Install dependencies:

    uv sync

## Commands

Scan:

    uv run dftr scan /path/to/music

Diagnose:

    uv run dftr doctor /path/to/music

Rename:

    uv run dftr fix /path/to/music

## Project Status

Version: 0.0.1

The project is already usable for real-world library cleanup but remains highly experimental.

Always keep backups before performing large renames.

## License

GNU General Public License v3.0 (GPL-3.0)

## Why?

Because life's too short to manually rename ten thousand FLAC albums.

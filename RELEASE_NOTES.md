# dontfeartheripper v0.1.1

The first release that feels production-ready.

This release introduces complete cover art management, MusicBrainz integration, automatic artwork retrieval and download planning while preserving the project's dry-run-first philosophy.

---

## Highlights

### Cover Art Management

Find missing artwork:

    dftr cover /music

Lookup candidates:

    dftr cover /music --fetch

Preview downloads:

    dftr cover /music --plan

Download artwork:

    dftr cover /music --yes

---

## New Features

### Missing Cover Detection

Detect missing artwork for:

- albums
- compilations
- soundtracks

Recursive artwork detection is supported.

Recognized filenames:

    cover.*
    folder.*
    front.*
    artwork.*
    albumart.*

Supported formats:

    jpg
    jpeg
    png

---

### MusicBrainz Integration

Automatic release matching through MusicBrainz.

---

### Cover Art Archive Integration

Automatic artwork retrieval through Cover Art Archive.

---

### Download Planning

Generate a complete cover download plan before writing files.

Example:

    dftr cover /music --plan

---

### Cover Downloads

Download artwork directly into album directories.

Example:

    dftr cover /music --yes

Progress reporting:

    [1/7] Album -> OK

Summary:

    Downloaded: 7
    Failed: 0

---

### Jellyfin Compatibility

Downloaded artwork is normalized to:

    cover.jpg

Compatible with:

- Jellyfin
- Plex
- Kodi
- Navidrome

---

## Performance

MusicBrainz lookup strategy redesigned.

Development library:

    ~48s
    ->
    ~12s

while maintaining identical cover discovery results.

---

## Existing Features

- Library scanning
- Diagnostics
- Statistics
- Quality analysis
- Metadata repair
- Directory renaming
- Rollback support
- JSON output

---

## Test Status

    15 passed
    0 failed

---

## Remaining Manual Cases

The following albums still require manual investigation:

- NoM (Nuisance of Majority) - Brains, Monkeys and the New World Order
- The Outer Worlds 2 Soundtrack

No suitable MusicBrainz cover match was found.

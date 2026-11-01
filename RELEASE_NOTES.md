# dontfeartheripper v0.1.4

## Highlights

v0.1.4 introduces the foundation for container-aware metadata recovery.

The project now contains four major subsystems:

- Recursive Library Discovery
- Container Engine
- Cover Management
- Metadata Recovery Engine

---

## Metadata Recovery Engine

New:

- TrackMetadata abstraction
- format-independent metadata model
- recovery candidate builder
- repair operation builder
- container-aware recovery
- container metadata context resolution

Recovery priority:

1. local metadata
2. container metadata
3. album.nfo
4. TOC/CUE metadata
5. MusicBrainz

Local metadata always wins.

---

## Container Engine

Supported container types:

- artist_container
- disc_container
- edition_container
- soundtrack_container
- generic_container

Features:

- recursive container discovery
- nested container discovery
- root-container detection
- container relationships
- container metadata
- jellyfin collection foundation

Generated:

- .dftr-container.json
- collection.nfo
- poster.jpg

Container metadata includes:

- container_id
- parent_container
- container_type
- album_count
- container_depth

---

## Cover Management

- MusicBrainz integration
- Cover Art Archive integration
- recursive artwork lookup
- download planning
- automatic cover downloads

Commands:

    dftr cover
    dftr cover --fetch
    dftr cover --plan
    dftr cover --yes

---

## Recursive Discovery

Recursive library scanning now supports:

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

## Testing

    46 passed
    0 failed

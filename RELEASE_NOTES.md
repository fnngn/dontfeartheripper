# dontfeartheripper v0.1.5

## Highlights

v0.1.5 introduces a complete metadata recovery engine and significantly improves container modelling.

The project now contains:

- Recursive Discovery Engine
- Cover Management Engine
- Container Engine
- Metadata Recovery Engine
- Jellyfin Collection Foundation

---

## Metadata Recovery Engine

New:

- TrackMetadata abstraction
- format-independent metadata model
- recovery candidate builder
- full metadata recovery operations
- NFO-first metadata recovery
- nearest album.nfo discovery
- container-aware recovery
- container-aware repair

Recovery priority:

1. local metadata
2. album.nfo
3. container metadata
4. TOC/CUE
5. MusicBrainz

Local metadata always wins.

Successful real-world recovery examples:

- Frostpunk → Piotr Musiał
- Cyberpunk 2077 → Marcin Przybylowicz
- The Thaumaturge → Agnieszka Wlazly

---

## Container Engine

Supported container types:

- artist_container
- disc_container
- format_container
- soundtrack_container
- generic_container

Features:

- recursive discovery
- nested containers
- root-container selection
- container relationships
- container metadata generation

Generated files:

- .dftr-container.json
- collection.nfo
- poster.jpg

Metadata includes:

- container_id
- parent_container
- container_type
- album_count
- container_depth
- schema_version
- generated_version

---

## Jellyfin Collection Foundation

Container processing generates:

- collection.nfo
- poster.jpg

Collection metadata includes:

- title
- uniqueid
- overview
- type
- albumcount
- depth
- dateadded

---

## Cover Management

Features:

- MusicBrainz integration
- Cover Art Archive integration
- recursive artwork discovery
- download planning
- cover download support

Supported commands:

    dftr cover
    dftr cover --fetch
    dftr cover --plan
    dftr cover --yes

---

## Quality Engine

Improvements:

- container-aware quality analysis
- reduced container-related false positives
- improved metadata source attribution
- NFO-aware quality evaluation

---

## Testing

54 passed
0 failed

# dontfeartheripper v0.1.3

## Container Engine

dontfeartheripper now supports recursive container discovery and metadata generation.

### Supported Container Types

- artist_container
- disc_container
- edition_container
- soundtrack_container
- generic_container

### Recursive Discovery

- nested containers
- multi-level hierarchies
- root container selection
- parent/child relationships

### Container Metadata

Generated:

- .dftr-container.json

Metadata includes:

- container_id
- parent_container
- container_type
- album_count
- container_depth
- schema_version
- generated_by
- generated_version

### Jellyfin Collection Foundation

Generated:

- collection.nfo
- poster.jpg

collection.nfo includes:

- title
- uniqueid
- overview
- type
- albumcount
- depth
- dateadded

Container artwork is generated automatically from existing child album artwork.

### Commands

    dftr container
    dftr container --yes

### Test Status

31 passed
0 failed

# dontfeartheripper v0.1.3

## Container Engine

### Recursive Container Discovery

Supported container types:

- artist_container
- disc_container
- edition_container
- soundtrack_container
- generic_container

### Container Metadata

Generated metadata now includes:

- container_id
- parent_container
- container_type
- album_count
- container_depth
- schema_version
- generated_by
- generated_version

### Jellyfin Collection Foundation

`dftr container --yes` now generates:

- .dftr-container.json
- collection.nfo
- poster.jpg

for detected root containers.

### collection.nfo

Generated fields:

- title
- uniqueid
- overview
- type
- albumcount
- depth
- dateadded

### Container Artwork

Container artwork is automatically generated from the first available child album cover.

### Testing

31 tests passing.

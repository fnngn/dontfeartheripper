# dontfeartheripper

Music library cleanup and repair tool for FLAC collections.

## Features

### Discovery

    dftr scan
    dftr scan --json

### Diagnostics

    dftr doctor
    dftr doctor --json

### Statistics

    dftr stats
    dftr stats --json

### Quality Analysis

    dftr quality
    dftr quality --json

### Quality Repair

    dftr repair
    dftr repair --json
    dftr repair --yes

Rollback:

    dftr repair-undo

### Folder Repair

Preview:

    dftr fix

Apply:

    dftr fix --yes

Rollback:

    dftr undo

## JSON API

Machine readable output:

    dftr scan --json
    dftr doctor --json
    dftr stats --json
    dftr quality --json
    dftr repair --json

All JSON formats contain:

    schema_version

## Repair Rules

Current automatic repairs:

- missing_artist
- various_uppercase
- various_mixed

## Safety

All repair operations:

- default to dry-run
- support rollback
- are validated before execution

## Testing

Run tests:

    uv run pytest -v

Current test coverage:

- repair_missing_artist
- repair_various_albumartist
- container_is_never_repaired
- quality_score_improves
- scan_prefers_high_quality_flac_data

## License

GPL-3.0

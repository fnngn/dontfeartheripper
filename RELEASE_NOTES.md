# dontfeartheripper v0.1.8

## Highlights

- Added a persistent SQLite library index for album, track, artist, genre,
  and collection metadata.
- Reworked collection detection to inspect each directory once and batch
  database writes during the initial index build.
- Added mouse-wheel scrolling for long TUI reports.
- Build the index on first use; subsequent searches and library reports load
  indexed metadata instead of repeatedly scanning all music files.
- Use indexed full-text search for quick substring matching.
- Refresh the index explicitly with `dftr scan /music` or `r` in the TUI.

## Index details

- Store the database in the user's XDG cache directory, outside the music
  library; `DFTR_DATABASE_PATH` can override its location.
- Build or refresh the index transactionally and retain the prior valid index
  if a refresh is interrupted.
- Invalidate the affected index when tag repairs or folder renames are applied
  or undone.

## Verification

    102 tests passing

---

# dontfeartheripper v0.1.7

## Highlights

- Added live progress indicators for long-running scans, artwork lookups,
  downloads, collection operations, and maintenance tasks.
- Added cooperative, safe cancellation with `Esc` or `Ctrl-C` in the TUI and
  `Ctrl-C` in CLI commands.
- Added library search for songs, albums, artists, genres, and local
  collections.
- Improved recovery safety with atomic file writes and durable rollback logs
  for tag repairs and folder renames.

## Search and progress

- Search is case-insensitive, checks audio tags and file/collection names,
  and falls back to filenames when track titles are missing.
- Read genre tags across supported audio formats, including WAV, APE, and WV.
- Show clearer operation descriptions, determinate progress, and counters in
  the TUI and interactive CLI.
- Run long TUI actions in the background so the interface stays responsive.

## Safe cancellation

- Stop work at safe checkpoints rather than interrupting a file or network
  operation midway.
- Preserve rollback records as tag repairs and folder renames complete, so
  completed changes can be undone after an interruption.
- Write generated metadata and downloaded artwork atomically to avoid
  half-written files.
- Warn that completed Jellyfin API requests may already have changed server
  state and should be reviewed before retrying.

## Verification

    97 tests passing

---

# dontfeartheripper v0.1.6

## Highlights

- Added a keyboard-driven terminal UI with a dashboard and grouped menus for
  library review, artwork, collections, and maintenance.
- Added native Jellyfin collection generation and synchronization through the
  Jellyfin API. Preview is the default; publishing requires explicit
  confirmation.
- Added safe matching for nested and multi-disc album folders, and preserved
  existing Jellyfin collection artwork.
- Improved recursive audio metadata scanning, artwork handling, NFO
  generation, and directory rename/undo operations.

## Jellyfin collections

- Match local album folders to Jellyfin music albums and show unmatched paths
  before making changes.
- Create or synchronize native Jellyfin collections, including memberships
  and available collection artwork.
- Support a separate Jellyfin library root for differing server mount paths.
- Use Jellyfin's MediaBrowser authorization and image-upload formats.
- Keep existing collection posters rather than overwriting them.

Run a read-only preview:

    dftr jellyfin-collections /path/to/music

Apply the plan only after reviewing it:

    dftr jellyfin-collections /path/to/music --yes

## Terminal UI

- Added `dftr tui /path/to/music`.
- Grouped actions under Overview, Library, Artwork, Collections, and
  Maintenance, with Escape/Backspace navigation back to the main menu.
- Use the terminal's default colors and background.
- Keep destructive operations behind confirmation prompts.

## Other improvements and fixes

- Scan supported audio formats for tags and track counts, not only FLAC.
- Avoid overwriting existing cover files; scope cover downloads to the
  requested library and report skipped downloads.
- Escape generated NFO XML correctly and report invalid NFO files.
- Preserve PNG poster extensions and handle uppercase FLAC extensions.
- Add safe rename previews, collision checks, and undo support.
- Improve MusicBrainz query normalization and metadata quality reporting.

## Verification

    85 tests passing

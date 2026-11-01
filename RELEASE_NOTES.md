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

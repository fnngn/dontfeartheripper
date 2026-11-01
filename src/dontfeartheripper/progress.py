from collections.abc import Callable
from threading import Event


ProgressCallback = Callable[[str, int | None, int | None], None]


class OperationCancelled(Exception):
    """Raised when an operation reaches a safe cancellation point."""


class CancellationToken:
    def __init__(self) -> None:
        self._event = Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()

    def raise_if_cancelled(self) -> None:
        if self.cancelled:
            raise OperationCancelled("Operation cancelled safely.")


def humanize_progress_message(message: str) -> str:
    """Turn internal progress details into concise labels for the UI."""
    def path_name(value):
        return value.replace("\\", "/").rstrip("/").rsplit("/", 1)[-1]

    if message.startswith("Searching track tags · "):
        return f"Checking track details · {message[23:]}"
    if message == "Searching track titles, artists, and genres":
        return "Searching song, artist, and genre tags"
    if message.startswith("Searching "):
        path = message[10:]
        if "/" in path or "\\" in path:
            return f"Finding music files · {path_name(path)}"
    if message.startswith("Scanning ") and message.endswith(" folders"):
        category = message[9:-8]
        return f"Scanning the {category} section"
    if message.startswith("Read tags: "):
        return f"Reading album tags · {message[11:]}"
    if message.startswith("Scan complete: "):
        return f"Library scan complete · {message[15:]}"
    if message.startswith("Checking audio files: "):
        return f"Checking music files · {message[22:]}"
    if message.startswith("Checking artwork files: "):
        return f"Looking through artwork · {message[24:]}"
    if message.startswith("Checking artwork folders: "):
        return f"Looking through artwork folders · {message[26:]}"
    if message.startswith("Checking repair rules: "):
        return f"Checking tag repairs · {message[23:]}"
    if message.startswith("Checking metadata recovery: "):
        return f"Checking saved metadata · {message[29:]}"
    if message.startswith("Inspecting containers: "):
        return f"Finding collections · {path_name(message[23:])}"
    if message.startswith("Writing container files: "):
        return f"Saving collection files · {message[25:]}"
    if message.startswith("Found ") and message.endswith(" containers"):
        return message.replace(" containers", " collections")
    if message.startswith("Loading Jellyfin "):
        return "Loading your Jellyfin music library"
    if message.startswith("Loaded ") and " Jellyfin " in message:
        count, item_type = message.split(" Jellyfin ", 1)
        return f"{count} {item_type} from Jellyfin"
    if message.startswith("Matching albums: "):
        return f"Matching collection · {message[17:]}"
    if message.startswith("Matching "):
        return f"Matching albums · {message[9:].replace(': ', ' · ', 1)}"
    if message.startswith("Planned "):
        return f"Prepared collection · {message[8:]}"
    if message.startswith("Publishing collection: "):
        return f"Publishing collection · {message[23:]}"
    if message.startswith("Added albums to "):
        return f"Added albums · {message[16:]}"
    if message.startswith("Removed stale albums from "):
        return f"Removed outdated albums · {message[26:]}"
    if message.startswith("Created collection "):
        return f"Created collection · {message[19:]}"
    if message.startswith("Uploaded artwork for "):
        return f"Added collection artwork · {message[21:]}"
    if message.startswith("Published "):
        return f"Published collection · {message[10:]}"
    if message.startswith("Checking artwork: "):
        return f"Checking album artwork · {message[18:]}"
    if message.startswith("Cover lookup: "):
        album = message[14:].split(" -> ", 1)[0]
        return f"Looking up artwork · {album}"
    if message.startswith("Using cached match: "):
        return f"Using saved artwork result · {message[20:]}"
    if message.startswith("Keeping existing cover: "):
        return f"Keeping existing artwork · {message[24:]}"
    if message.startswith("Downloaded cover: "):
        return f"Downloaded artwork · {message[18:]}"
    if message.startswith("Cover download failed: "):
        return f"Artwork download failed · {message[23:]}"
    if message.startswith("Renaming "):
        return f"Renaming folder · {message[9:]}"
    if message.startswith("Restoring "):
        return f"Restoring folder · {message[10:]}"
    if message.startswith("Renamed "):
        return f"Renamed folder · {message[8:]}"
    if message.startswith("Restored "):
        return f"Restored folder · {message[9:]}"
    if message.startswith("Updating tags: "):
        return f"Updating track tags · {message[15:]}"
    if message.startswith("Updated tags: "):
        return f"Updated track tags · {message[14:]}"
    if message.startswith("Restoring tags: "):
        return f"Restoring track tags · {message[16:]}"
    if message.startswith("Restored tags: "):
        return f"Restored track tags · {message[15:]}"
    if message.startswith("Preparing "):
        return f"Getting ready · {message[10:]}"
    return message


def report_progress(
    callback: ProgressCallback | None,
    message: str,
    current: int | None = None,
    total: int | None = None,
) -> None:
    if callback is not None:
        callback(message, current, total)

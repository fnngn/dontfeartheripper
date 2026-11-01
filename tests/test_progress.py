from dontfeartheripper.progress import humanize_progress_message


def test_humanized_scan_progress_shortens_long_paths():
    message = humanize_progress_message(
        "Searching /music/albums/artist/album"
    )

    assert message == "Finding music files · album"


def test_humanized_tag_progress_explains_the_operation():
    message = humanize_progress_message("Updating tags: 01 - Song.flac")

    assert message == "Updating track tags · 01 - Song.flac"


def test_humanized_search_progress_keeps_its_meaning():
    message = humanize_progress_message(
        "Searching track titles, artists, and genres"
    )

    assert message == "Searching song, artist, and genre tags"


def test_humanized_jellyfin_progress_reads_naturally():
    message = humanize_progress_message("Loaded 25 Jellyfin albums")

    assert message == "Loaded 25 albums from Jellyfin"

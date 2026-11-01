from dontfeartheripper.nfo import parse_album_nfo


def test_malformed_album_nfo_logs_a_warning(tmp_path, caplog):
    nfo = tmp_path / "album.nfo"
    nfo.write_text("<album>", encoding="utf-8")

    metadata = parse_album_nfo(nfo)

    assert metadata["album"] is None
    assert "Could not parse album NFO" in caplog.text

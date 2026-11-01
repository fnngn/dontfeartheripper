import base64
from pathlib import Path

import pytest

from dontfeartheripper.jellyfin import (
    JellyfinClient,
    JellyfinError,
    apply_jellyfin_collection_plan,
    build_jellyfin_collection_plan,
    generate_jellyfin_collections,
)


class FakeJellyfin:
    def __init__(self, albums=None, collections=None, members=None):
        self.albums = albums or []
        self.collections = collections or []
        self.members = members or {}
        self.calls = []

    def items(self, item_type, *, parent_id=None):
        if parent_id:
            return self.members.get(parent_id, [])
        if item_type == "MusicAlbum":
            return self.albums
        if item_type == "BoxSet":
            return self.collections
        raise AssertionError(item_type)

    def create_collection(self, name, item_ids):
        self.calls.append(("create", name, item_ids))
        return "new-collection-id"

    def add_items(self, collection_id, item_ids):
        self.calls.append(("add", collection_id, item_ids))

    def remove_items(self, collection_id, item_ids):
        self.calls.append(("remove", collection_id, item_ids))

    def upload_primary_image(self, collection_id, image_path):
        self.calls.append(("image", collection_id, image_path))


def make_container(root, *, artwork=False):
    collection = root / "album" / "Example Artist"
    first = collection / "First Album"
    second = collection / "Second Album"
    first.mkdir(parents=True)
    second.mkdir()
    (first / "track.flac").touch()
    (second / "track.flac").touch()
    image = first / "cover.jpg"
    if artwork:
        image.write_bytes(b"image-data")
    return {
        "path": collection,
        "children": [
            {
                "type": "album",
                "name": "First Album",
                "path": "First Album",
            },
            {
                "type": "album",
                "name": "Second Album",
                "path": "Second Album",
            },
        ],
    }


def test_plan_matches_jellyfin_albums_by_library_relative_path(tmp_path):
    library = tmp_path / "library"
    container = make_container(library)
    client = FakeJellyfin(
        albums=[
            {
                "Id": "album-one",
                "Path": "/music/Example Artist/First Album",
            },
            {
                "Id": "album-two",
                "Path": "/music/Example Artist/Second Album",
            },
        ]
    )

    plan = build_jellyfin_collection_plan(
        [container],
        client,
        library,
    )

    assert plan[0]["name"] == "Example Artist"
    assert plan[0]["item_ids"] == ["album-one", "album-two"]
    assert plan[0]["matched_count"] == 2
    assert plan[0]["missing_paths"] == []


def test_server_root_maps_local_library_to_jellyfin_path(tmp_path):
    library = tmp_path / "library"
    container = make_container(library)
    client = FakeJellyfin(
        albums=[
            {
                "Id": "album-one",
                "Path": "/srv/music/album/Example Artist/First Album",
            },
            {
                "Id": "album-two",
                "Path": "/srv/music/album/Example Artist/Second Album",
            },
        ]
    )

    plan = build_jellyfin_collection_plan(
        [container],
        client,
        library,
        server_root="/srv/music",
    )

    assert plan[0]["matched_count"] == 2


def test_server_root_can_map_category_as_a_mount_detail(tmp_path):
    library = tmp_path / "library"
    container = make_container(library)
    client = FakeJellyfin(
        albums=[
            {
                "Id": "album-one",
                "Path": "/srv/music/Example Artist/First Album",
            },
            {
                "Id": "album-two",
                "Path": "/srv/music/Example Artist/Second Album",
            },
        ]
    )

    plan = build_jellyfin_collection_plan(
        [container],
        client,
        library,
        server_root="/srv/music",
    )

    assert plan[0]["matched_count"] == 2


def test_multidisc_directories_match_one_jellyfin_album(tmp_path):
    library = tmp_path / "local" / "Musik"
    container_path = library / "compilation" / "Cat Stevens - Discography"
    album_name = (
        "(1970) Cat Stevens - Mona Bone Jakon "
        "(Super Deluxe) [16Bit-44.1kHz]"
    )
    container = {
        "path": container_path,
        "children": [
            {
                "type": "container",
                "name": album_name,
                "children": [
                    {
                        "type": "album",
                        "name": f"Disc {number}",
                        "path": f"{album_name}/Disc {number}",
                    }
                    for number in range(1, 5)
                ],
            }
        ],
    }
    for number in range(1, 5):
        (container_path / album_name / f"Disc {number}").mkdir(
            parents=True
        )
    server_path = (
        "/media/nas/media/Musik/compilation/"
        f"Cat Stevens - Discography/{album_name}"
    )
    client = FakeJellyfin(
        albums=[{"Id": "mona-bone-jakon", "Path": server_path}]
    )

    plan = build_jellyfin_collection_plan(
        [container],
        client,
        library,
    )

    assert plan[0]["item_ids"] == ["mona-bone-jakon"]
    assert plan[0]["matched_count"] == 1
    assert plan[0]["album_count"] == 1
    assert plan[0]["missing_paths"] == []


def test_nested_soundtrack_disc_folders_match_parent_album(tmp_path):
    library = tmp_path / "local" / "Musik"
    container_path = (
        library / "soundtrack" / "Cyberpunk 2077 Bonus Content"
    )
    container = {
        "path": container_path,
        "children": [
            {
                "type": "container",
                "name": "soundtrack",
                "children": [
                    {
                        "type": "container",
                        "name": "mp3",
                        "children": [
                            {
                                "type": "album",
                                "name": f"cd{number}",
                                "path": f"soundtrack/mp3/cd{number}",
                            }
                            for number in (1, 2)
                        ],
                    }
                ],
            }
        ],
    }
    for number in (1, 2):
        (container_path / "soundtrack" / "mp3" / f"cd{number}").mkdir(
            parents=True
        )
    client = FakeJellyfin(
        albums=[
            {
                "Id": "cyberpunk-bonus",
                "Path": (
                    "/media/nas/media/Musik/soundtrack/"
                    "Cyberpunk 2077 Bonus Content/soundtrack/mp3"
                ),
            }
        ]
    )

    plan = build_jellyfin_collection_plan(
        [container],
        client,
        library,
    )

    assert plan[0]["item_ids"] == ["cyberpunk-bonus"]
    assert plan[0]["matched_count"] == 1
    assert plan[0]["album_count"] == 1
    assert plan[0]["missing_paths"] == []


def test_ambiguous_path_suffix_is_not_guessed(tmp_path):
    library = tmp_path / "library"
    container = make_container(library)
    client = FakeJellyfin(
        albums=[
            {
                "Id": "one",
                "Path": "/music-a/Example Artist/First Album",
            },
            {
                "Id": "two",
                "Path": "/music-b/Example Artist/First Album",
            },
            {
                "Id": "three",
                "Path": "/music-a/Example Artist/Second Album",
            },
        ]
    )

    plan = build_jellyfin_collection_plan(
        [container],
        client,
        library,
    )

    assert plan[0]["item_ids"] == ["three"]
    assert plan[0]["missing_paths"] == [
        str(library / "album/Example Artist/First Album")
    ]


def test_plan_calculates_collection_membership_delta(tmp_path):
    library = tmp_path / "library"
    container = make_container(library, artwork=True)
    client = FakeJellyfin(
        albums=[
            {
                "Id": "one",
                "Path": "/music/Example Artist/First Album",
            },
            {
                "Id": "two",
                "Path": "/music/Example Artist/Second Album",
            },
        ],
        collections=[
            {
                "Id": "collection-id",
                "Name": "Example Artist",
                "ImageTags": {"Primary": "existing-poster"},
            }
        ],
        members={
            "collection-id": [
                {"Id": "one"},
                {"Id": "stale"},
            ]
        },
    )

    plan = build_jellyfin_collection_plan(
        [container],
        client,
        library,
    )

    assert plan[0]["collection_id"] == "collection-id"
    assert plan[0]["add_ids"] == ["two"]
    assert plan[0]["remove_ids"] == ["stale"]
    assert plan[0]["has_primary_image"]


def test_apply_creates_native_jellyfin_collection_and_poster(
    tmp_path,
):
    container = make_container(tmp_path, artwork=True)
    client = FakeJellyfin()
    plan = [
        {
            "name": "Example Artist",
            "collection_id": None,
            "item_ids": ["one", "two"],
            "add_ids": ["one", "two"],
            "remove_ids": [],
            "missing_paths": [],
            "artwork_path": str(
                container["path"] / "First Album" / "cover.jpg"
            ),
            "album_count": 2,
            "matched_count": 2,
        }
    ]

    results = apply_jellyfin_collection_plan(plan, client)

    assert results == [
        {
            "name": "Example Artist",
            "status": "created",
            "collection_id": "new-collection-id",
            "matched_count": 2,
            "missing_paths": [],
            "artwork_uploaded": True,
            "existing_artwork_preserved": False,
        }
    ]
    assert client.calls == [
        ("create", "Example Artist", ["one", "two"]),
        (
            "image",
            "new-collection-id",
            container["path"] / "First Album" / "cover.jpg",
        ),
    ]


def test_apply_synchronizes_existing_collection_members():
    client = FakeJellyfin()
    plan = [
        {
            "name": "Existing Collection",
            "collection_id": "collection-id",
            "item_ids": ["keep", "add"],
            "add_ids": ["add"],
            "remove_ids": ["remove"],
            "missing_paths": [],
            "artwork_path": None,
            "album_count": 2,
            "matched_count": 2,
        }
    ]

    result = apply_jellyfin_collection_plan(plan, client)

    assert result[0]["status"] == "updated"
    assert client.calls == [
        ("add", "collection-id", ["add"]),
        ("remove", "collection-id", ["remove"]),
    ]


def test_sync_preserves_existing_jellyfin_collection_poster(
    tmp_path,
):
    container = make_container(tmp_path, artwork=True)
    client = FakeJellyfin()
    plan = [
        {
            "name": "Example Artist",
            "collection_id": "collection-id",
            "has_primary_image": True,
            "item_ids": ["one"],
            "add_ids": [],
            "remove_ids": [],
            "missing_paths": [],
            "artwork_path": str(
                container["path"] / "First Album" / "cover.jpg"
            ),
            "album_count": 1,
            "matched_count": 1,
        }
    ]

    result = apply_jellyfin_collection_plan(plan, client)

    assert result[0]["existing_artwork_preserved"]
    assert not result[0]["artwork_uploaded"]
    assert all(call[0] != "image" for call in client.calls)
    assert [call[0] for call in client.calls] == ["add", "remove"]


def test_apply_skips_collections_without_matched_albums():
    client = FakeJellyfin()
    plan = [
        {
            "name": "Unmatched",
            "collection_id": None,
            "item_ids": [],
            "add_ids": [],
            "remove_ids": [],
            "missing_paths": ["album path"],
            "artwork_path": None,
            "album_count": 1,
            "matched_count": 0,
        }
    ]

    result = apply_jellyfin_collection_plan(plan, client)

    assert result[0]["status"] == "skipped"
    assert client.calls == []


def test_generator_defaults_to_plan_only(tmp_path, monkeypatch):
    client = FakeJellyfin()
    monkeypatch.setattr(
        "dontfeartheripper.jellyfin.JellyfinClient",
        lambda *args: client,
    )
    container = make_container(tmp_path)
    client.albums = [
        {
            "Id": "one",
            "Path": f"/music/Example Artist/First Album",
        },
        {
            "Id": "two",
            "Path": f"/music/Example Artist/Second Album",
        },
    ]

    report = generate_jellyfin_collections(
        [container],
        "http://jellyfin.local",
        "test-key",
        tmp_path,
    )

    assert report["mode"] == "dry_run"
    assert report["collections"][0]["matched_count"] == 2
    assert client.calls == []


class FakeResponse:
    ok = True
    status_code = 200
    text = ""

    def json(self):
        return {"Id": "created-id"}


class FakeSession:
    def __init__(self):
        self.headers = {}
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return FakeResponse()


def test_jellyfin_client_uses_mediabrowser_auth_and_encoded_query_params():
    session = FakeSession()
    client = JellyfinClient(
        "https://jellyfin.example/base",
        "secret-token",
        session=session,
    )

    collection_id = client.create_collection(
        "Artist & Friends",
        ["one", "two"],
    )

    assert collection_id == "created-id"
    assert session.headers["Authorization"] == (
        'MediaBrowser Token="secret-token", '
        'Client="dontfeartheripper", '
        'Device="dontfeartheripper", '
        'DeviceId="dontfeartheripper", Version="1.0"'
    )
    method, url, kwargs = session.calls[0]
    assert method == "POST"
    assert url == "https://jellyfin.example/base/Collections"
    assert kwargs["params"] == {
        "name": "Artist & Friends",
        "ids": "one,two",
    }
    assert "secret-token" not in url


def test_upload_primary_image_sends_base64_encoded_image_body(tmp_path):
    session = FakeSession()
    client = JellyfinClient(
        "https://jellyfin.example",
        "secret-token",
        session=session,
    )
    image = tmp_path / "poster.jpg"
    image.write_bytes(b"jpeg-image-data")

    client.upload_primary_image("collection-id", image)

    method, url, kwargs = session.calls[0]
    assert method == "POST"
    assert url.endswith("/Items/collection-id/Images/Primary")
    assert kwargs["headers"] == {"Content-Type": "image/jpeg"}
    assert kwargs["data"] == base64.b64encode(b"jpeg-image-data")


def test_jellyfin_http_errors_are_reported_without_api_key():
    class ErrorResponse(FakeResponse):
        ok = False
        status_code = 401
        text = "Unauthorized"

    class ErrorSession(FakeSession):
        def request(self, method, url, **kwargs):
            return ErrorResponse()

    client = JellyfinClient(
        "https://jellyfin.example",
        "secret-token",
        session=ErrorSession(),
    )

    with pytest.raises(JellyfinError, match="HTTP 401"):
        client.items("MusicAlbum")


def test_duplicate_local_container_names_fail_safely(tmp_path):
    first = make_container(tmp_path / "one")
    second = make_container(tmp_path / "two")
    client = FakeJellyfin()

    with pytest.raises(JellyfinError, match="Multiple local containers"):
        build_jellyfin_collection_plan(
            [first, second],
            client,
            tmp_path,
        )


def test_image_type_is_rejected_if_unsupported(tmp_path):
    image = tmp_path / "poster.svg"
    image.write_text("<svg/>")
    client = JellyfinClient(
        "https://jellyfin.example",
        "test-token",
        session=FakeSession(),
    )

    with pytest.raises(JellyfinError, match="Unsupported"):
        client.upload_primary_image("collection-id", image)


def test_tui_exposes_read_only_and_confirmed_collection_actions(
    tmp_path,
    monkeypatch,
):
    from dontfeartheripper.tui import (
        CONFIRM_ACTIONS,
        MENU_GROUPS,
        _action_lines,
    )

    monkeypatch.setenv("JELLYFIN_URL", "https://jellyfin.example")
    monkeypatch.setenv("JELLYFIN_API_KEY", "test-token")
    monkeypatch.setattr(
        "dontfeartheripper.tui.detect_containers",
        lambda root: [],
    )
    monkeypatch.setattr(
        "dontfeartheripper.tui.generate_jellyfin_collections",
        lambda *args, **kwargs: {
            "collections": [],
            "results": [],
        },
    )

    menu_ids = {
        action
        for entries in MENU_GROUPS.values()
        for action, _ in entries
    }

    assert "jellyfin-preview" in menu_ids
    assert "jellyfin-apply" in menu_ids
    assert "jellyfin-apply" in CONFIRM_ACTIONS
    assert _action_lines(
        "jellyfin-preview",
        tmp_path,
        [],
    )[0] == "Jellyfin collection plan"


def test_tui_groups_actions_and_esc_returns_to_main_menu(
    tmp_path,
    monkeypatch,
):
    import curses

    from dontfeartheripper.tui import MAIN_MENU, MENU_GROUPS, _main

    class FakeScreen:
        def __init__(self):
            self.drawn = []
            self.keys = iter((10, 10, 27, 10, ord("j"), 10, ord("q")))

        def erase(self):
            pass

        def getmaxyx(self):
            return 24, 80

        def addnstr(self, y, x, text, width, attr=0):
            self.drawn.append((y, x, text[:width]))

        def refresh(self):
            pass

        def keypad(self, enabled):
            pass

        def getch(self):
            return next(self.keys)

    monkeypatch.setattr(curses, "curs_set", lambda visibility: None)
    monkeypatch.setattr(curses, "start_color", lambda: None)
    monkeypatch.setattr(curses, "use_default_colors", lambda: None)
    monkeypatch.setattr(curses, "init_pair", lambda *args: None)
    monkeypatch.setattr(curses, "color_pair", lambda pair: pair)
    monkeypatch.setattr(
        "dontfeartheripper.tui.scan_library",
        lambda root: [],
    )
    screen = FakeScreen()

    _main(screen, tmp_path)

    assert [group for group, _ in MAIN_MENU] == [
        "overview",
        "library",
        "artwork",
        "collections",
        "maintenance",
        "quit",
    ]
    assert "dashboard" in {
        action for action, _ in MENU_GROUPS["overview"]
    }
    assert "jellyfin-preview" in {
        action for action, _ in MENU_GROUPS["collections"]
    }
    assert any("MAIN MENU" in text for _, _, text in screen.drawn)
    assert any("OVERVIEW" in text for _, _, text in screen.drawn)
    assert any("Back to main menu" in text for _, _, text in screen.drawn)


def test_tui_uses_default_background_and_playlist_layout(
    tmp_path,
    monkeypatch,
):
    import curses

    from dontfeartheripper.tui import _main

    class FakeScreen:
        def __init__(self):
            self.drawn = []

        def erase(self):
            pass

        def getmaxyx(self):
            return 24, 80

        def addnstr(self, y, x, text, width, attr=0):
            self.drawn.append((y, x, text[:width]))

        def refresh(self):
            pass

        def keypad(self, enabled):
            pass

        def getch(self):
            return ord("q")

    pair_calls = []
    monkeypatch.setattr(curses, "curs_set", lambda visibility: None)
    monkeypatch.setattr(curses, "start_color", lambda: None)
    monkeypatch.setattr(curses, "use_default_colors", lambda: None)
    monkeypatch.setattr(
        curses,
        "init_pair",
        lambda pair, foreground, background: pair_calls.append(
            (pair, foreground, background)
        ),
    )
    monkeypatch.setattr(curses, "color_pair", lambda pair: pair)
    monkeypatch.setattr(
        "dontfeartheripper.tui.scan_library",
        lambda root: [],
    )
    screen = FakeScreen()

    _main(screen, tmp_path)

    assert pair_calls == [
        (1, curses.COLOR_CYAN, -1),
        (2, curses.COLOR_CYAN, -1),
        (3, curses.COLOR_YELLOW, -1),
    ]
    assert any("MAIN MENU" in text for _, _, text in screen.drawn)
    assert any("SECTIONS" in text for _, _, text in screen.drawn)

import logging
from pathlib import Path
import xml.etree.ElementTree as ET


logger = logging.getLogger(__name__)


def parse_album_nfo(path: Path) -> dict:

    try:

        tree = ET.parse(path)
        root = tree.getroot()

        title = root.findtext(
            "title"
        )

        year = root.findtext(
            "year"
        )

        genre = root.findtext(
            "genre"
        )

        artists = [
            artist.text
            for artist in root.findall(
                "artist"
            )
            if artist.text
        ]

        albumartists = [
            artist.text
            for artist in root.findall(
                "albumartist"
            )
            if artist.text
        ]

        disc = None

        track = root.find("track")

        if track is not None:

            disc_text = track.findtext(
                "disc"
            )

            if disc_text:

                try:

                    disc = int(
                        disc_text
                    )

                except ValueError:

                    pass

        return {
            "title": title,
            "album": title,
            "artist":
                artists[0]
                if artists
                else None,
            "artists": artists,
            "albumartist":
                albumartists[0]
                if albumartists
                else None,
            "albumartists":
                albumartists,
            "year": year,
            "genre": genre,
            "disc": disc,
        }

    except (ET.ParseError, OSError, UnicodeError) as exc:
        logger.warning("Could not parse album NFO %s: %s", path, exc)
        return {
            "title": None,
            "album": None,
            "artist": None,
            "artists": [],
            "albumartist": None,
            "albumartists": [],
            "year": None,
            "genre": None,
            "disc": None,
        }

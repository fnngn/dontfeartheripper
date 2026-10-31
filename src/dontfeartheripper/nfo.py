from pathlib import Path
import xml.etree.ElementTree as ET


def parse_album_nfo(path: Path) -> dict:
    try:
        tree = ET.parse(path)
        root = tree.getroot()

        title = root.findtext("title")
        albumartist = root.findtext("albumartist")

        disc = None

        track = root.find("track")
        if track is not None:
            disc_text = track.findtext("disc")
            if disc_text:
                try:
                    disc = int(disc_text)
                except ValueError:
                    pass

        return {
            "title": title,
            "albumartist": albumartist,
            "disc": disc,
        }

    except Exception:
        return {
            "title": None,
            "albumartist": None,
            "disc": None,
        }

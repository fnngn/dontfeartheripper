import requests


def coverartarchive_cover(mbid):

    try:

        response = requests.get(
            f"https://coverartarchive.org/release/{mbid}",
            timeout=10,
        )

        if response.status_code != 200:
            return None

        data = response.json()

        images = data.get(
            "images",
            [],
        )

        if not images:
            return None

        image = images[0]

        return image.get("image")

    except requests.RequestException:
        return None


def discogs_cover(artist, album):

    #
    # Placeholder for v0.1.2
    #

    return None

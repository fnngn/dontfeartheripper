def sanitize_filename(value: str) -> str:
    replacements = {
        ":": " -",
        "/": "-",
        "\\": "-",
        "*": "",
        "?": "",
        "<": "",
        ">": "",
        "|": "-",
        '"': "",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    value = " ".join(value.split())

    return value.strip()

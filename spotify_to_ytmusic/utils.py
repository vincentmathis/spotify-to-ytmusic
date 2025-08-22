import re
from rapidfuzz import fuzz


def normalize(string: str) -> str:
    if not string:
        return ""
    string = string.lower()
    # remove (feat. ...), (featuring ...), (with ...) in () or []
    string = re.sub(r"[\(\[].*?(feat\.|featuring|with).*?[\)\]]", "", string)
    # remove common suffixes like " - Remastered", " - Live", " - 2011 Version"
    string = re.sub(r"(original mix|remaster(ed)?|live|version.*)", "", string)
    # only alnum + space
    string = "".join(c for c in string if c.isalnum() or c.isspace())
    return string.strip()


def ranked_matches(song, results):
    """Return all YTMusic results scored against the target song, sorted best-first"""
    target = f"{normalize(song['title'])} {normalize(song['artist'])}".strip()
    scored = []

    for r in results:
        if "videoId" not in r:
            continue
        candidate_title = normalize(r["title"])
        candidate_artist = (
            normalize(r["artists"][0]["name"]) if r.get("artists") else ""
        )
        candidate = f"{candidate_title} {candidate_artist}".strip()
        score = fuzz.ratio(target, candidate)
        scored.append((r, score))

    return sorted(scored, key=lambda x: x[1], reverse=True)

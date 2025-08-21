from rapidfuzz import fuzz


def normalize(s: str) -> str:
    return "".join(c for c in s.lower() if c.isalnum() or c.isspace()).strip()


def best_match(song, results):
    target_title = normalize(song["title"])
    target_artist = normalize(song["artist"])
    best_score = 0
    best_result = None
    for r in results:
        if "videoId" not in r:
            continue
        yt_title = normalize(r["title"])
        yt_artist = normalize(r["artists"][0]["name"]) if r.get("artists") else ""
        score = (
            fuzz.ratio(target_title, yt_title) + fuzz.ratio(target_artist, yt_artist)
        ) / 2
        if score > best_score:
            best_score = score
            best_result = r
    return best_result, best_score

from datetime import datetime
import feedparser


def fetch_feed(rss_url: str):
    feed = feedparser.parse(rss_url)
    if feed.bozo:
        raise ValueError("Failed to parse RSS feed")
    return feed


def normalize_entries(feed):
    entries = []
    for entry in feed.entries:
        guid = entry.get("guid") or entry.get("id") or entry.get("link")
        published = entry.get("published_parsed") or entry.get("updated_parsed")
        if published:
            published_at = datetime(*published[:6])
        else:
            published_at = datetime.utcnow()

        audio_url = None
        for link in entry.get("links", []):
            if link.get("type", "").startswith("audio"):
                audio_url = link.get("href")
                break

        if not audio_url and entry.get("enclosures"):
            audio_url = entry.enclosures[0].get("href")

        entries.append(
            {
                "guid": guid,
                "title": entry.get("title", ""),
                "description": entry.get("summary", ""),
                "published_at": published_at,
                "audio_url": audio_url or "",
            }
        )
    return entries

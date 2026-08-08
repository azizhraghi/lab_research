import httpx
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from email.utils import parsedate_to_datetime
import datetime


def _parse_feed_date(raw: str | None) -> datetime.datetime:
    """Parse a feed publish date, falling back to now() when missing/invalid.

    RSS 2.0 <pubDate> is RFC 822 (e.g. "Wed, 02 Oct 2024 13:00:00 GMT"); Atom
    <published>/<updated> is ISO 8601. Previously every article got utcnow(),
    which made the whole feed look "published right now" — a data-quality defect.
    """
    if not raw or not raw.strip():
        return datetime.datetime.utcnow()
    raw = raw.strip()
    # Try RFC 822 (RSS pubDate) first.
    try:
        return parsedate_to_datetime(raw)
    except (TypeError, ValueError, Exception):
        pass
    # Then ISO 8601 (Atom published/updated). Strip a trailing Z so fromisoformat
    # (pre-3.11) accepts it.
    try:
        iso = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
        return datetime.datetime.fromisoformat(iso)
    except ValueError:
        return datetime.datetime.utcnow()


async def fetch_rss_feed(url: str) -> List[Dict[str, Any]]:
    """Fetch and parse an RSS/Atom feed."""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()

            root = ET.fromstring(response.text)
            items = []

            # Atom
            for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
                title = entry.find("{http://www.w3.org/2005/Atom}title")
                link = entry.find("{http://www.w3.org/2005/Atom}link")
                summary = entry.find("{http://www.w3.org/2005/Atom}summary")
                published = entry.find("{http://www.w3.org/2005/Atom}published")
                updated = entry.find("{http://www.w3.org/2005/Atom}updated")
                date_raw = (published.text if published is not None else None) \
                    or (updated.text if updated is not None else None)

                items.append({
                    "title": title.text if title is not None else "No Title",
                    "url": link.attrib.get('href') if link is not None else None,
                    "abstract": summary.text if summary is not None else None,
                    "authors": [],
                    "published_at": _parse_feed_date(date_raw),
                    "doi": None
                })

            # RSS 2.0
            for item in root.findall(".//item"):
                title = item.find("title")
                link = item.find("link")
                desc = item.find("description")
                pub_date = item.find("pubDate")

                items.append({
                    "title": title.text if title is not None else "No Title",
                    "url": link.text if link is not None else None,
                    "abstract": desc.text if desc is not None else None,
                    "authors": [],
                    "published_at": _parse_feed_date(pub_date.text if pub_date is not None else None),
                    "doi": None
                })

            return items
        except Exception as e:
            print(f"Error fetching RSS {url}: {e}")
            return []

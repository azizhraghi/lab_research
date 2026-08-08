"""ArXiv fetcher for the veille (scientific watch) agent.

ArXiv exposes an Atom API at http://export.arxiv.org/api/query that returns
results in Atom XML. This fetcher runs a search query and yields the same dict
shape the RSS/Atom scraper produces (title/url/abstract/authors/published_at/doi),
so the collection loop in VeilleAgent treats it identically.

ArXiv API etiquette: one request every 3 seconds. We pass max_results (default 25)
to stay polite. Callers (the agent loop) add their own sleeps between sources.
"""
from __future__ import annotations

import datetime
from typing import Any, Dict, List

import httpx
import xml.etree.ElementTree as ET

ATOM_NS = "{http://www.w3.org/2005/Atom}"
ARXIV_API_URL = "http://export.arxiv.org/api/query"
ARXIV_NS = "{http://arxiv.org/schemas/atom}"


def _parse_arxiv_date(raw: str | None) -> datetime.datetime | None:
    """ArXiv <published> is ISO 8601 e.g. 2024-09-30T12:34:56Z."""
    if not raw or not raw.strip():
        return None
    raw = raw.strip()
    try:
        iso = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
        return datetime.datetime.fromisoformat(iso)
    except ValueError:
        return None


async def fetch_arxiv(search_query: str, max_results: int = 25) -> List[Dict[str, Any]]:
    """Search ArXiv and return parsed entries.

    `search_query` uses ArXiv's query syntax, e.g.:
      - "all:water stress irrigation"
      - "cat:cs.AI AND all:groundwater"
    See https://info.arxiv.org/help/api/user-manual.html#query_details.
    """
    params = {
        "search_query": search_query,
        "start": 0,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    # ArXiv's API etiquette asks for a descriptive User-Agent and at most one
    # request every 3 seconds. Anonymous clients get throttled hard (HTTP 429).
    headers = {"User-Agent": "LRSTE-Veille/1.0 (research lab scientific watch; mailto:admin@lrste.example)"}
    async with httpx.AsyncClient(follow_redirects=True, headers=headers) as client:
        try:
            response = await client.get(ARXIV_API_URL, params=params, timeout=30.0)
            response.raise_for_status()
            root = ET.fromstring(response.text)
        except Exception as e:
            print(f"[veille:arxiv] Error querying ArXiv for '{search_query}': {e}")
            return []

    items: List[Dict[str, Any]] = []
    for entry in root.findall(f"{ATOM_NS}entry"):
        title_el = entry.find(f"{ATOM_NS}title")
        summary_el = entry.find(f"{ATOM_NS}summary")
        published_el = entry.find(f"{ATOM_NS}published")
        id_el = entry.find(f"{ATOM_NS}id")

        # The entry <id> is the abstract page URL; the PDF <link> is separate.
        url = id_el.text.strip() if id_el is not None and id_el.text else None
        pdf_url = None
        for link in entry.findall(f"{ATOM_NS}link"):
            if link.attrib.get("title") == "pdf":
                pdf_url = link.attrib.get("href")
                break

        # Authors
        authors: List[str] = []
        for author in entry.findall(f"{ATOM_NS}author"):
            name_el = author.find(f"{ATOM_NS}name")
            if name_el is not None and name_el.text:
                authors.append(name_el.text.strip())

        # DOI (optional in ArXiv)
        doi_el = entry.find(f"{ARXIV_NS}doi")
        doi = doi_el.text.strip() if doi_el is not None and doi_el.text else None

        title = (title_el.text.strip() if title_el is not None and title_el.text
                 else "No Title")
        # ArXiv abstracts have messy whitespace.
        abstract = (summary_el.text.strip() if summary_el is not None and summary_el.text
                    else None)

        items.append({
            "title": title,
            "url": url,
            "abstract": abstract,
            "authors": authors,
            "published_at": _parse_arxiv_date(published_el.text if published_el is not None else None),
            "doi": doi,
            # Extra metadata kept for provenance; the Article model ignores unknown keys.
            "pdf_url": pdf_url,
            "source_type": "arxiv",
        })

    return items

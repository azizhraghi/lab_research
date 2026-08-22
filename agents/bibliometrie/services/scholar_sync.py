"""Google Scholar publications fetch via scholarly — the extract half of the
Scholar sync, mirroring orcid_sync.py.

Was dead code (imported nowhere) until the publication ETL existed in
publication_sync.py. scholarly is synchronous and blocks, so everything runs in
a thread via asyncio.to_thread. Proxy setup deliberately does NOT happen here:
the bibliometrie agent configures scholarly's process-wide proxy at startup
(ScraperAPI when configured, direct requests otherwise), and scholarly is a
singleton — fetching here reuses whatever the agent set up.

Unlike the old version, a failed fetch raises ScholarUnavailable instead of
returning [] — an empty list must mean "the profile lists no works", never
"Scholar rate-limited us and we pretended it worked".
"""
from typing import Any, Dict, List
import asyncio

from agents.bibliometrie.services.orcid_sync import normalise_doi


class ScholarUnavailable(RuntimeError):
    """Scholarly could not fetch the profile — blocked, rate-limited, or unknown id."""


async def fetch_scholar_works(scholar_id: str) -> List[Dict[str, Any]]:
    """Fetch a Google Scholar author's publications as Publication-shaped dicts."""

    def _fetch():
        try:
            from scholarly import scholarly

            author = scholarly.search_author_id(scholar_id)
            author = scholarly.fill(author, sections=["publications"])
        except Exception as exc:
            raise ScholarUnavailable(
                f"Google Scholar fetch failed for {scholar_id}: "
                f"{type(exc).__name__}: {exc}"
            ) from exc

        works: List[Dict[str, Any]] = []
        for pub in author.get("publications", []):
            bib = pub.get("bib", {})
            title = (bib.get("title") or "").strip()
            if not title:
                # An untitled entry is unusable for dedup or display.
                continue
            try:
                year = int(bib.get("pub_year"))
            except (TypeError, ValueError):
                year = None
            raw_doi = bib.get("doi")
            works.append({
                "title": title,
                "year": year,
                # Scholar summaries do not distinguish article/conference/book.
                "type": "article",
                # bib "citation" is Scholar's venue line (often a journal
                # abbreviation) — the closest thing to a journal we get.
                "journal": bib.get("journal") or bib.get("citation") or None,
                "doi": normalise_doi(raw_doi) if raw_doi else None,
                "citation_count": int(pub.get("num_citations", 0) or 0),
                "source": "scholar",
            })
        return works

    return await asyncio.to_thread(_fetch)

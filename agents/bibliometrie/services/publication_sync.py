"""Publication ETL — turn fetched works into biblio_publications rows.

Before this module, `biblio_publications` had no writer in application code: the
only inserts were the fabricated demo rows in seed_dev.py. The CV route queried
the table and always got zero rows, so every generated CV claimed the researcher
had no publications. This is the load half of the ORCID extract.

Two rules shape the upsert:

**Publications are shared, links are per-researcher.** `biblio_publications.doi`
is UNIQUE, and co-authors in the same lab will sync the same paper. So a work is
matched to an existing row first and only inserted when genuinely new; the
per-researcher fact lives in `biblio_researcher_publications`. Syncing two
co-authors yields one publication row and two links, which is what makes the
lab's publication count meaningful rather than double-counted.

**Matching prefers the DOI and falls back to title+year.** A DOI is exact. When
a work has none (theses, reports, some conference papers) we compare on
lowercased title plus year, which is imperfect but beats inserting a duplicate
on every run. Re-running a sync must be idempotent.

`citation_count` is deliberately left alone: ORCID does not report citations, so
overwriting it with 0 would destroy whatever Scopus/Scholar recorded.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.bibliometrie.models import Publication, Researcher, ResearcherPublication
from agents.bibliometrie.services.orcid_sync import fetch_orcid_works

# Columns worth backfilling onto a publication row that already exists but is
# missing detail. Never overwrite a populated value with None.
ENRICHABLE_FIELDS = ("journal", "year", "type", "abstract")


async def _find_existing(
    db: AsyncSession, work: Dict[str, Any]
) -> Optional[Publication]:
    """Locate an existing publication for this work, by DOI then title+year."""
    doi = work.get("doi")
    if doi:
        found = await db.execute(select(Publication).where(Publication.doi == doi))
        return found.scalar_one_or_none()

    title = (work.get("title") or "").strip()
    if not title:
        return None
    stmt = select(Publication).where(
        func.lower(Publication.title) == title.lower(),
        Publication.doi.is_(None),
    )
    year = work.get("year")
    stmt = stmt.where(Publication.year == year) if year is not None else stmt
    found = await db.execute(stmt.limit(1))
    return found.scalar_one_or_none()


def _enrich(publication: Publication, work: Dict[str, Any]) -> bool:
    """Fill blank columns from the incoming work. Returns True if anything changed."""
    changed = False
    for field in ENRICHABLE_FIELDS:
        incoming = work.get(field)
        if incoming is None or getattr(publication, field, None) is not None:
            continue
        setattr(publication, field, incoming)
        changed = True
    return changed


async def _link(
    db: AsyncSession, researcher_id: int, publication_id: int
) -> bool:
    """Attach a publication to a researcher. Returns True if a new link was made."""
    existing = await db.execute(
        select(ResearcherPublication).where(
            ResearcherPublication.researcher_id == researcher_id,
            ResearcherPublication.publication_id == publication_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        return False
    db.add(
        ResearcherPublication(
            researcher_id=researcher_id,
            publication_id=publication_id,
            # ORCID does not expose author order on a work summary, so leaving
            # this NULL is honest; inventing 1 would assert first authorship.
            author_position=None,
        )
    )
    return True


async def upsert_works_for_researcher(
    db: AsyncSession,
    researcher: Researcher,
    works: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Load fetched works, sharing publication rows across co-authors.

    Commits once at the end so a partial failure leaves nothing half-written.
    """
    created = updated = linked = already_linked = 0
    # Two works in one payload can resolve to the same row (e.g. duplicate DOIs
    # from different asserting sources). Cache to avoid a second insert attempt
    # against the UNIQUE doi constraint within a single flush.
    seen: Dict[Tuple[str, Any], Publication] = {}

    for work in works:
        key = ("doi", work["doi"]) if work.get("doi") else (
            "title", ((work.get("title") or "").lower(), work.get("year"))
        )
        publication = seen.get(key) or await _find_existing(db, work)

        if publication is None:
            publication = Publication(
                title=work["title"],
                doi=work.get("doi"),
                journal=work.get("journal"),
                year=work.get("year"),
                type=work.get("type"),
                source=work.get("source", "orcid"),
                citation_count=0,
            )
            db.add(publication)
            created += 1
        elif _enrich(publication, work):
            updated += 1

        seen[key] = publication
        # Needed before linking: a freshly added row has no id until flushed.
        await db.flush()

        if await _link(db, researcher.id, publication.id):
            linked += 1
        else:
            already_linked += 1

    await db.commit()
    return {
        "researcher_id": researcher.id,
        "source": "orcid",
        "works_found": len(works),
        "publications_created": created,
        "publications_enriched": updated,
        "links_created": linked,
        "links_already_present": already_linked,
    }


async def sync_orcid_publications(
    db: AsyncSession, researcher: Researcher
) -> Dict[str, Any]:
    """Fetch a researcher's ORCID works and load them.

    Propagates OrcidUnavailable so the caller can distinguish an outage or a bad
    ORCID iD from a record that genuinely lists no works.
    """
    works = await fetch_orcid_works(researcher.orcid_id or "")
    return await upsert_works_for_researcher(db, researcher, works)

"""ORCID public-API works fetcher.

Reads a researcher's own publication list from https://pub.orcid.org/v3.0. The
public API needs no key and no scraping: an ORCID record is the researcher's
self-curated list, which makes it the most authoritative source we have for
"what did this person publish" (Scholar and Scopus give us metrics, not works).

Two things about the response shape drive the parsing below, both verified
against a live record rather than inferred:

1. **`group` is already deduplicated.** ORCID clusters the same work asserted by
   several sources (Crossref, the publisher, the author) into one group with
   several `work-summary` entries. Iterating groups and taking the first summary
   therefore yields unique works — iterating summaries would double-count.
2. **Almost every nested field can be null**, including `publication-date`,
   `publication-date.year`, `journal-title` and `title.title`. The keys are
   present with a null value, so `dict.get(k, {})` returns None rather than the
   default and a chained `.get()` raises AttributeError. Every access here goes
   through `_value()` / `_dig()` for that reason.

A transport or HTTP failure raises OrcidUnavailable instead of returning [], so
a caller can tell "this researcher has no works on file" (empty list, a fact)
apart from "ORCID did not answer" (an outage, not a fact about the researcher).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx

ORCID_API_BASE = "https://pub.orcid.org/v3.0"
REQUEST_TIMEOUT_SECONDS = 30.0

# Work types ORCID may report; we keep the raw value but normalise the casing.
# See https://info.orcid.org/ufaqs/what-work-types-does-orcid-support/


class OrcidUnavailable(RuntimeError):
    """ORCID could not be reached, or answered with an error status."""


def _dig(node: Any, *keys: str) -> Any:
    """Walk nested dicts, tolerating None at any level.

    ORCID returns explicit nulls rather than omitting keys, so this returns None
    for a missing path instead of raising.
    """
    current = node
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _value(node: Any, *keys: str) -> Optional[str]:
    """Extract a scalar from ORCID's ``{"value": ...}`` wrapper objects."""
    found = _dig(node, *keys) if keys else node
    if isinstance(found, dict):
        found = found.get("value")
    if found is None:
        return None
    text = str(found).strip()
    return text or None


def normalise_doi(raw: str) -> Optional[str]:
    """Canonical bare-lowercase form of a DOI string, or None.

    The same paper arrives as "10.1234/ABC", "https://doi.org/10.1234/abc" and
    "doi:10.1234/abc" depending on the asserting source, and
    biblio_publications.doi is UNIQUE — so every loader normalises the same way.
    """
    doi = raw.strip().lower()
    for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.startswith(prefix):
            doi = doi[len(prefix):]
            break
    return doi.strip("/") or None


def _extract_doi(summary: Dict[str, Any]) -> Optional[str]:
    """Return the DOI from external-ids, normalised to bare lowercase form."""
    ids = _dig(summary, "external-ids", "external-id")
    if not isinstance(ids, list):
        return None
    for entry in ids:
        if not isinstance(entry, dict):
            continue
        if (entry.get("external-id-type") or "").lower() != "doi":
            continue
        raw = _value(entry, "external-id-normalized") or _value(entry, "external-id-value")
        if not raw:
            continue
        return normalise_doi(raw)
    return None


def _parse_year(summary: Dict[str, Any]) -> Optional[int]:
    year = _value(summary, "publication-date", "year")
    if year is None:
        return None
    try:
        return int(year)
    except (TypeError, ValueError):
        return None


def _parse_summary(summary: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Normalise one work-summary into our Publication shape, or None if unusable."""
    title = _value(summary, "title", "title")
    if not title:
        # A work with no readable title is not worth storing.
        return None
    return {
        "title": title,
        "year": _parse_year(summary),
        "type": (_dig(summary, "type") or "unknown"),
        "journal": _value(summary, "journal-title"),
        "doi": _extract_doi(summary),
        "url": _value(summary, "url"),
        "put_code": _dig(summary, "put-code"),
        "source": "orcid",
    }


async def fetch_orcid_works(orcid_id: str) -> List[Dict[str, Any]]:
    """Fetch the works on a public ORCID record.

    Returns one dict per distinct work. Raises OrcidUnavailable on transport
    failure or a non-200 status — including 404, which means the ORCID iD itself
    is wrong and the caller should say so rather than report "no publications".
    """
    if not orcid_id or not orcid_id.strip():
        raise OrcidUnavailable("No ORCID iD on file for this researcher.")

    orcid_id = orcid_id.strip()
    url = f"{ORCID_API_BASE}/{orcid_id}/works"
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = await client.get(url, headers={"Accept": "application/json"})
    except httpx.RequestError as exc:
        raise OrcidUnavailable(
            f"Could not reach ORCID ({type(exc).__name__}). Try again shortly."
        ) from exc

    if response.status_code == 404:
        raise OrcidUnavailable(f"ORCID has no public record for iD {orcid_id}.")
    if response.status_code != 200:
        raise OrcidUnavailable(
            f"ORCID returned HTTP {response.status_code} for iD {orcid_id}."
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise OrcidUnavailable("ORCID returned a response that was not JSON.") from exc

    works: List[Dict[str, Any]] = []
    seen_dois: set[str] = set()
    for group in (_dig(payload, "group") or []):
        summaries = _dig(group, "work-summary")
        if not isinstance(summaries, list) or not summaries:
            continue
        # Groups are already per-work; the extra summaries are duplicate
        # assertions of the same paper by different sources.
        parsed = _parse_summary(summaries[0])
        if parsed is None:
            continue
        doi = parsed.get("doi")
        if doi:
            if doi in seen_dois:
                continue
            seen_dois.add(doi)
        works.append(parsed)
    return works

"""Scopus / Elsevier author metrics fetcher.

Elsevier exposes the Author Retrieval API at https://api.elsevier.com/content/author.
It returns the h-index and total citation count for an author, looked up either by
Scopus author ID (preferred — the `scopus_id` column in biblio_researchers) or by an
ORCID. A name-based search is also supported via the Author Search API, used as a
last resort when neither ID is available.

Requires an Elsevier API key (https://dev.elsevier.com/api-keys/manage/). The key
is read from the SCOPUS_API_KEY or ELSEVIER_API_KEY env var; without it this module
returns None and the bibliometrie agent falls back to the next source in its chain.

Output: a dict with the keys the agent's metric pipeline expects:
  {h_index, citation_count, scopus_id, source}
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests

SCOPUS_API_KEY_ENV_VARS = ("SCOPUS_API_KEY", "ELSEVIER_API_KEY")
AUTHOR_RETRIEVAL_URL = "https://api.elsevier.com/content/author"
AUTHOR_SEARCH_URL = "https://api.elsevier.com/content/search/author"


def get_scopus_api_key() -> Optional[str]:
    return next((os.getenv(n) for n in SCOPUS_API_KEY_ENV_VARS if os.getenv(n)), None)


def _build_headers() -> Dict[str, str]:
    """Common headers for Elsevier API requests."""
    key = get_scopus_api_key()
    return {
        "Accept": "application/json",
        "X-ELS-APIKey": key or "",
        # Elsevier asks for an insttoken for some institutional tiers; optional here.
    }


def fetch_scopus_author_by_id(scopus_id: str) -> Optional[Dict[str, Any]]:
    """Look up an author directly by Scopus author ID (e.g. '57203507479').

    Returns a normalized metrics dict or None on any failure / missing key.
    """
    if not get_scopus_api_key():
        return None
    # The endpoint expects the scopus_id prefixed with the author URI scheme.
    aid = scopus_id if scopus_id.startswith("AUTHOR_ID:") else scopus_id
    params = {"view": "METRICS", "field": "author-retieval,h-index,citation-count,document-count"}
    try:
        resp = requests.get(
            f"{AUTHOR_RETRIEVAL_URL}",
            params={"author_id": aid, **params},
            headers=_build_headers(),
            timeout=20,
        )
        if resp.status_code == 401:
            print("[biblio:scopus] Invalid API key (401). Check SCOPUS_API_KEY.")
            return None
        if resp.status_code == 429:
            print("[biblio:scopus] Rate limited (429). Back off and retry later.")
            return None
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[biblio:scopus] Author retrieval failed for {aid}: {type(e).__name__}: {e}")
        return None

    return _parse_author_response(resp.json(), scopus_id=aid)


def fetch_scopus_author_by_orcid(orcid: str) -> Optional[Dict[str, Any]]:
    """Look up an author by ORCID via the Author Retrieval API."""
    if not get_scopus_api_key() or not orcid:
        return None
    try:
        resp = requests.get(
            AUTHOR_RETRIEVAL_URL,
            params={"orcid": orcid, "view": "METRICS"},
            headers=_build_headers(),
            timeout=20,
        )
        if resp.status_code in (401, 404):
            return None
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[biblio:scopus] ORCID lookup failed for {orcid}: {type(e).__name__}: {e}")
        return None
    return _parse_author_response(resp.json())


def search_scopus_author_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Search the Scopus Author Search API by name and return the best match's metrics.

    Used only when neither a Scopus ID nor an ORCID is available.
    """
    if not get_scopus_api_key() or not name:
        return None
    try:
        resp = requests.get(
            AUTHOR_SEARCH_URL,
            params={"query": f"AUTHOR-NAME({name})"},
            headers=_build_headers(),
            timeout=20,
        )
        if resp.status_code in (401, 404):
            return None
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"[biblio:scopus] Author search failed for '{name}': {type(e).__name__}: {e}")
        return None

    data = resp.json()
    entries = (
        data.get("search-results", {}).get("entry", [])
        if isinstance(data, dict)
        else []
    )
    if not entries:
        return None
    # Pick the candidate with the most documents as a proxy for "best match".
    best = max(
        entries,
        key=lambda e: int(e.get("document-count", "0") or 0),
    )
    scopus_id = best.get("dc:identifier", "").replace("AUTHOR_ID:", "")
    if not scopus_id:
        return None
    # The search entry carries h-index + citedby-count directly in some responses;
    # otherwise re-fetch via the metrics endpoint for accurate numbers.
    h_index = _safe_int(best.get("h-index"))
    citations = _safe_int(best.get("citedby-count"))
    if h_index is not None and citations is not None:
        return {
            "h_index": h_index,
            "citation_count": citations,
            "scopus_id": scopus_id,
            "source": "scopus",
        }
    return fetch_scopus_author_by_id(scopus_id)


def _parse_author_response(payload: Dict[str, Any], scopus_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Normalize the Author Retrieval JSON into our metrics dict."""
    try:
        core = (
            payload.get("author-retrieval-response", {})
            .get("coredata", {})
        )
    except AttributeError:
        return None
    h_index = _safe_int(core.get("h-index"))
    citations = _safe_int(core.get("citation-count"))
    documents = _safe_int(core.get("document-count"))
    sid = scopus_id or (
        payload.get("author-retrieval-response", {}).get("@_fa", "") or None
    )
    if h_index is None and citations is None:
        return None
    return {
        "h_index": h_index,
        "citation_count": citations,
        "document_count": documents,
        "scopus_id": sid,
        "source": "scopus",
    }


def _safe_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def fetch_scopus_metrics(
    scopus_id: Optional[str] = None,
    orcid: Optional[str] = None,
    name: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Top-level Scopus metrics lookup with the same fallback order as the agent.

    Tries: Scopus ID → ORCID → name search. Returns None if no API key is set or
    nothing is found, so callers can fall through to the next data source.
    """
    if not get_scopus_api_key():
        return None
    if scopus_id:
        result = fetch_scopus_author_by_id(scopus_id)
        if result:
            return result
    if orcid:
        result = fetch_scopus_author_by_orcid(orcid)
        if result:
            return result
    if name:
        return search_scopus_author_by_name(name)
    return None

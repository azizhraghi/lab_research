# -*- coding: utf-8 -*-
"""Bibliometrie Agent – Researcher profile management and scholarly metrics.

OVERWRITTEN with Friend 1's richer version (16.8KB, 4x larger).
Adapted to use the monorepo's shared BaseAgent, schemas, and imports.
"""
from __future__ import annotations
from typing import Any, List, Optional
from datetime import datetime, timezone
import os
import inspect
import requests

from shared.base_agent import BaseAgent
from shared.schemas import Event, AgentAction, ActionResult
from agents.bibliometrie.services.scopus_sync import fetch_scopus_metrics as _fetch_scopus_metrics_raw

SCRAPERAPI_KEY_ENV_VARS = ("SCRAPERAPI_KEY", "SCHOLAR_SCRAPERAPI_KEY")
SEMANTIC_SCHOLAR_AUTHOR_SEARCH_URL = "https://api.semanticscholar.org/graph/v1/author/search"
OPENALEX_AUTHOR_SEARCH_URL = "https://api.openalex.org/authors"

# ── Scholarly optional import (graceful degradation) ──────────────────

try:
    import httpx
    from scholarly import scholarly, ProxyGenerator
    from scholarly import _proxy_generator as scholarly_proxy_module
except Exception as exc:
    httpx = None
    scholarly = None
    ProxyGenerator = None
    scholarly_proxy_module = None
    SCHOLARLY_IMPORT_ERROR: Exception | None = exc
else:
    SCHOLARLY_IMPORT_ERROR = None


# ── Pydantic bridge profile ───────────────────────────────────────────
#
# This is NOT a storage model: it is the transient profile the metric fetchers
# (Scholar → Scopus → Semantic Scholar → OpenAlex) mutate in place before
# run_sync_for_researcher writes the values back to BiblioIndicator rows.
# Storage lives in agents/bibliometrie/models.py (the DB models).

from pydantic import BaseModel, Field
from uuid import uuid4


class Researcher(BaseModel):
    """Fetch-session profile for one researcher."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    email: Optional[str] = None
    orcid: Optional[str] = None
    google_scholar_id: Optional[str] = None
    scopus_id: Optional[str] = None
    h_index: Optional[int] = None
    citation_count: Optional[int] = None
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ── Helper functions (from Friend 1) ─────────────────────────────────

def _httpx_supports_proxies() -> bool:
    if httpx is None:
        return False
    return "proxies" in inspect.signature(httpx.Client).parameters


def _first_proxy(proxies: Any) -> str | None:
    if isinstance(proxies, dict):
        return (
            proxies.get("https://")
            or proxies.get("http://")
            or proxies.get("https")
            or proxies.get("http")
        )
    return proxies


def _normalize_name(name: str) -> str:
    return " ".join(name.casefold().split())


def _select_semantic_scholar_author(candidates: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    if not candidates:
        return None
    normalized_name = _normalize_name(name)
    exact_matches = [c for c in candidates if _normalize_name(c.get("name", "")) == normalized_name]
    best_candidates = exact_matches or candidates
    return max(best_candidates, key=lambda c: (c.get("citationCount") or 0, c.get("paperCount") or 0))


def _select_openalex_author(candidates: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    if not candidates:
        return None
    normalized_name = _normalize_name(name)
    exact_matches = [c for c in candidates if _normalize_name(c.get("display_name", "")) == normalized_name]
    best_candidates = exact_matches or candidates
    return max(best_candidates, key=lambda c: (c.get("cited_by_count") or 0, c.get("works_count") or 0))


def _patched_new_session(self, **kwargs):
    """Compatibility patch for scholarly 1.7.x with modern httpx versions."""
    if httpx is None or scholarly_proxy_module is None:
        raise RuntimeError(f"scholarly is unavailable: {SCHOLARLY_IMPORT_ERROR}")

    init_kwargs = {"follow_redirects": True}
    init_kwargs.update(kwargs)
    proxies = {}

    if self._session:
        proxies = self._proxies
        self._close_session()

    self.got_403 = False

    if scholarly_proxy_module.FAKE_USERAGENT:
        with self._suppress_logger("fake_useragent"):
            user_agent = scholarly_proxy_module.UserAgent().random
    else:
        user_agent = scholarly_proxy_module.DEFAULT_USER_AGENT

    init_kwargs.update(
        headers={
            "accept-language": "en-US,en",
            "accept": "text/html,application/xhtml+xml,application/xml",
            "User-Agent": user_agent,
        }
    )

    if self._proxy_works:
        init_kwargs["proxies"] = proxies
        self._proxies = proxies
        if self.proxy_mode is scholarly_proxy_module.ProxyMode.SCRAPERAPI:
            init_kwargs["verify"] = False

    if "proxies" in init_kwargs and not _httpx_supports_proxies():
        proxy = _first_proxy(init_kwargs.pop("proxies"))
        if proxy:
            init_kwargs["proxy"] = proxy

    self._session = httpx.Client(**init_kwargs)
    self._webdriver = None
    return self._session


def _patch_scholarly_httpx_proxy() -> bool:
    if ProxyGenerator is None:
        return False
    ProxyGenerator._new_session = _patched_new_session
    return True


_patch_scholarly_httpx_proxy()


# ── The Agent ─────────────────────────────────────────────────────────

class BibliometrieAgent(BaseAgent):
    """Agent responsible for maintaining researcher profiles,
    computing bibliometric metrics, and generating CV PDFs."""

    name = "bibliometrie"
    permissions = ["biblio.read", "biblio.write"]
    requires_human_approval = ["biblio.update_cv_profile"]

    def __init__(self):
        super().__init__()
        self._setup_scholar_proxy()

    def _setup_scholar_proxy(self) -> None:
        if scholarly is None or ProxyGenerator is None:
            print(f"[{self.name}] Scholar unavailable: {SCHOLARLY_IMPORT_ERROR}")
            return

        api_key = next((os.getenv(n) for n in SCRAPERAPI_KEY_ENV_VARS if os.getenv(n)), None)
        if not api_key:
            print(f"[{self.name}] No ScraperAPI key configured; using direct Scholar requests")
            return

        try:
            pg = ProxyGenerator()
            if not pg.ScraperAPI(api_key):
                print(f"[{self.name}] ScraperAPI proxy setup failed; using direct Scholar requests")
                return
            scholarly.use_proxy(pg)
            print(f"[{self.name}] Scholar proxy configured successfully")
        except Exception as e:
            print(f"[{self.name}] Proxy setup failed: {e}")

    # ── JSON profile store (removed 2026-08-21) ────────────────────────
    # _load/_save_researchers, add/get/list_researcher, _match_researcher,
    # _regenerate_cv and update_all_metrics backed /api/biblio/profiles/*, a
    # parallel researcher store over a gitignored JSON file of fabricated
    # profiles. The DB-backed /researchers routes are the real ones.

    # ── Scholarly metrics fetching (multi-source fallback) ────────────

    def _fetch_semantic_scholar_metrics(self, researcher: Researcher) -> bool:
        try:
            response = requests.get(
                SEMANTIC_SCHOLAR_AUTHOR_SEARCH_URL,
                params={"query": researcher.name, "fields": "name,hIndex,citationCount,paperCount", "limit": 10},
                timeout=20,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"[{self.name}] Semantic Scholar fallback failed for {researcher.name}: {type(e).__name__}: {e}")
            return False

        author = _select_semantic_scholar_author(response.json().get("data", []), researcher.name)
        if author is None:
            print(f"[{self.name}] No Semantic Scholar profile found for: {researcher.name}")
            return False

        researcher.h_index = author.get("hIndex", researcher.h_index)
        researcher.citation_count = author.get("citationCount", researcher.citation_count)
        researcher.last_updated = datetime.now(timezone.utc)
        print(f"[{self.name}] {researcher.name}: h-index={researcher.h_index}, citations={researcher.citation_count} (Semantic Scholar)")
        return True

    def _fetch_openalex_metrics(self, researcher: Researcher) -> bool:
        try:
            response = requests.get(OPENALEX_AUTHOR_SEARCH_URL, params={"search": researcher.name, "per-page": 10}, timeout=20)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"[{self.name}] OpenAlex fallback failed for {researcher.name}: {type(e).__name__}: {e}")
            return False

        author = _select_openalex_author(response.json().get("results", []), researcher.name)
        if author is None:
            print(f"[{self.name}] No OpenAlex profile found for: {researcher.name}")
            return False

        summary_stats = author.get("summary_stats", {})
        researcher.h_index = summary_stats.get("h_index", researcher.h_index)
        researcher.citation_count = author.get("cited_by_count", researcher.citation_count)
        researcher.last_updated = datetime.now(timezone.utc)
        print(f"[{self.name}] {researcher.name}: h-index={researcher.h_index}, citations={researcher.citation_count} (OpenAlex)")
        return True

    def _fetch_scopus_metrics(self, researcher: Researcher) -> bool:
        """Elsevier Scopus author metrics (h-index + citations).

        Requires an Elsevier API key (SCOPUS_API_KEY / ELSEVIER_API_KEY). Without
        one this is a no-op and returns False so the caller falls through to the
        next source. The lookup order mirrors the agent's overall philosophy:
        explicit Scopus ID → ORCID → name search. The `scopus_id` column on
        biblio_researchers finally has a consumer.
        """
        from agents.bibliometrie.services.scopus_sync import get_scopus_api_key
        if not get_scopus_api_key():
            # Fast no-op when unconfigured — never log spam on the common case.
            return False
        result = _fetch_scopus_metrics_raw(
            scopus_id=getattr(researcher, "scopus_id", None),
            orcid=researcher.orcid,
            name=researcher.name,
        )
        if not result:
            print(f"[{self.name}] Scopus lookup found nothing for {researcher.name}")
            return False
        researcher.h_index = result.get("h_index", researcher.h_index)
        researcher.citation_count = result.get("citation_count", researcher.citation_count)
        if result.get("scopus_id") and not getattr(researcher, "scopus_id", None):
            # The name search may have resolved a Scopus ID we didn't have.
            try:
                researcher.scopus_id = result["scopus_id"]
            except Exception:
                pass
        researcher.last_updated = datetime.now(timezone.utc)
        print(f"[{self.name}] {researcher.name}: h-index={researcher.h_index}, "
              f"citations={researcher.citation_count} (Scopus)")
        return True

    def _fetch_fallback_metrics(self, researcher: Researcher) -> bool:
        # Scopus is the most authoritative for institutions with an Elsevier
        # subscription, so it goes first when a key is configured. Without a key
        # it's a fast no-op (returns False immediately) and the chain continues.
        return (
            self._fetch_scopus_metrics(researcher)
            or self._fetch_semantic_scholar_metrics(researcher)
            or self._fetch_openalex_metrics(researcher)
        )

    def fetch_scholar_metrics(self, researcher: Researcher) -> Researcher:
        if scholarly is None:
            print(f"[{self.name}] Scholar lookup skipped for {researcher.name}: {SCHOLARLY_IMPORT_ERROR}")
            self._fetch_fallback_metrics(researcher)
            return researcher

        try:
            print(f"[{self.name}] Searching Google Scholar for: {researcher.name}")
            if researcher.google_scholar_id:
                author = scholarly.search_author_id(researcher.google_scholar_id)
            else:
                search_results = scholarly.search_author(researcher.name)
                author = next(search_results, None)

            if author is None:
                print(f"[{self.name}] No usable Scholar profile found for {researcher.name}; trying fallback sources")
                self._fetch_fallback_metrics(researcher)
                return researcher

            author = scholarly.fill(author)
            researcher.h_index = author.get("hindex", None)
            researcher.citation_count = author.get("citedby", None)
            researcher.google_scholar_id = author.get("scholar_id", researcher.google_scholar_id)
            researcher.last_updated = datetime.now(timezone.utc)
            print(f"[{self.name}] {researcher.name}: h-index={researcher.h_index}, citations={researcher.citation_count}")

        except Exception as e:
            print(f"[{self.name}] Scholar lookup failed for {researcher.name}: {type(e).__name__}: {e}")
            self._fetch_fallback_metrics(researcher)

        return researcher

    # ── DB-backed sync (router endpoint POST /api/biblio/researchers/{id}/sync)
    #
    # The router and the (now removed) Celery task both called this method, but
    # it was never defined → guaranteed AttributeError → HTTP 500. It bridges a
    # DB Researcher row into the agent's pydantic Researcher profile, runs the
    # existing 3-tier fetch (Scholar → Semantic Scholar → OpenAlex), and writes
    # the h_index / total_citations back to the BiblioIndicator table (which
    # existed but was never populated).
    async def run_sync_for_researcher(self, db, researcher_id: int) -> dict:
        from agents.bibliometrie.models import (
            Researcher as ResearcherModel, BiblioIndicator,
        )

        db_researcher = await db.get(ResearcherModel, researcher_id)
        if db_researcher is None:
            raise ValueError(f"Researcher {researcher_id} not found")

        # Bridge the DB row into the pydantic profile the fetchers expect, using
        # whichever identifier columns are populated to maximize match quality.
        profile = Researcher(
            name=db_researcher.name,
            email=db_researcher.email,
            google_scholar_id=db_researcher.scholar_id,
            orcid=db_researcher.orcid_id,
            scopus_id=db_researcher.scopus_id,
        )
        before = (profile.h_index, profile.citation_count)
        updated = self.fetch_scholar_metrics(profile)
        # Detect which tier actually populated the metrics, for provenance.
        if updated.google_scholar_id and updated.google_scholar_id == getattr(profile, "google_scholar_id", None):
            source = "scholar"
        elif updated.scopus_id:
            source = "scopus"
        else:
            source = "semantic_scholar_or_openalex"

        # Upsert the two indicators the platform actually computes
        # (agents/bibliometrie/services/indicators.py): h_index, total_citations.
        from sqlalchemy import select as _sa_select
        new_values = {
            "h_index": updated.h_index,
            "total_citations": updated.citation_count,
        }
        for metric_name, value in new_values.items():
            if value is None:
                continue
            stmt = _sa_select(BiblioIndicator).where(
                BiblioIndicator.researcher_id == researcher_id,
                BiblioIndicator.metric_name == metric_name,
            )
            row = (await db.execute(stmt)).scalar_one_or_none()
            if row is None:
                db.add(BiblioIndicator(
                    researcher_id=researcher_id,
                    metric_name=metric_name,
                    value=float(value),
                ))
            else:
                row.value = float(value)
                row.computed_at = datetime.now(timezone.utc)

        await db.commit()
        print(f"[{self.name}] Synced researcher {researcher_id} via {source}: "
              f"was {before}, now h={updated.h_index}, c={updated.citation_count}")
        return {
            "researcher_id": researcher_id,
            "source": source,
            "h_index": updated.h_index,
            "total_citations": updated.citation_count,
        }

    # ── Event handling ────────────────────────────────────────────────

    async def _handle_article_discovered(self, event: Event) -> None:
        """Link a veille-collected article to the lab researchers who wrote it.

        The pre-merge version appended to the JSON profile store nobody read.
        Now: an article carrying a DOI whose author list matches DB researchers
        becomes a real biblio_publications row (source="veille") linked through
        the same upsert the ORCID/Scholar imports use — DOI-normalised,
        idempotent, rows shared across co-authors. Articles without a DOI are
        skipped: an RSS title is not bibliographic evidence.
        """
        payload = event.payload
        doi = payload.get("doi")
        title = (payload.get("title") or "").strip()
        if not doi or not title:
            return
        authors = {a for a in (payload.get("authors") or []) if a}
        if not authors:
            return

        from sqlalchemy import select as _sa_select
        from shared.database import AsyncSessionLocal
        from agents.bibliometrie.models import Researcher as ResearcherModel
        from agents.bibliometrie.services.orcid_sync import normalise_doi
        from agents.bibliometrie.services.publication_sync import (
            upsert_works_for_researcher,
        )

        author_keys = {_normalize_name(a) for a in authors}
        work = {
            "title": title,
            "year": None,
            "type": "article",
            "journal": None,
            "doi": normalise_doi(doi),
            "source": "veille",
        }

        async with AsyncSessionLocal() as db:
            researchers = (
                await db.execute(_sa_select(ResearcherModel))
            ).scalars().all()
            matched = [
                r for r in researchers if _normalize_name(r.name) in author_keys
            ]
            if not matched:
                return
            for researcher in matched:
                result = await upsert_works_for_researcher(
                    db, researcher, [work], source="veille"
                )
                if result["links_created"] or result["publications_created"]:
                    print(
                        f"[{self.name}] Veille article linked to {researcher.name}: "
                        f"{title[:60]}"
                    )

    async def _setup_subscriptions(self):
        # Subscribe to the fanout stream and route article-discovery events to
        # the existing publication-append + CV-regeneration handler. This makes
        # the veille → bibliometrie chain real (vs. dead code before bus wiring).
        await self._subscribe("events", self._dispatch_event)

    async def _dispatch_event(self, event: Event) -> None:
        """Bus callback — filter to the event types this agent cares about."""
        try:
            if event.type in ("veille.article_collected", "article.discovered"):
                await self._handle_article_discovered(event)
        except Exception as e:
            print(f"[{self.name}] Error handling {event.type}: {e}")

    async def handle_event(self, event: Event) -> Optional[AgentAction]:
        if event.type == "article.discovered":
            await self._handle_article_discovered(event)
        return None

    async def execute_action(self, action: AgentAction) -> ActionResult:
        return ActionResult(
            action_id=action.id,
            status="completed",
            result_data={"message": "Action executed by BibliometrieAgent"},
        )


bibliometrie_agent = BibliometrieAgent()

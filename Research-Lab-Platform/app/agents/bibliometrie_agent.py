# -*- coding: utf-8 -*-
from __future__ import annotations
from app.core.base_agent import BaseAgent            
from app.core.event_bus import EventBus              
from app.schemas.events import Event                  
from app.schemas.bibliometrie import Researcher, Publication  
from typing import Any, Dict, List                         
from datetime import datetime, timezone
from app.agents.cv_generator import generate_cv      
import os                                             # for creating folders
import inspect
import json                                          
import os                                            
import requests

RESEARCHERS_FILE = "researchers.json"
SCRAPERAPI_KEY_ENV_VARS = ("SCRAPERAPI_KEY", "SCHOLAR_SCRAPERAPI_KEY")
SEMANTIC_SCHOLAR_AUTHOR_SEARCH_URL = "https://api.semanticscholar.org/graph/v1/author/search"
OPENALEX_AUTHOR_SEARCH_URL = "https://api.openalex.org/authors"

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
    exact_matches = [
        candidate
        for candidate in candidates
        if _normalize_name(candidate.get("name", "")) == normalized_name
    ]
    best_candidates = exact_matches or candidates

    return max(
        best_candidates,
        key=lambda candidate: (
            candidate.get("citationCount") or 0,
            candidate.get("paperCount") or 0,
        ),
    )


def _select_openalex_author(candidates: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    if not candidates:
        return None

    normalized_name = _normalize_name(name)
    exact_matches = [
        candidate
        for candidate in candidates
        if _normalize_name(candidate.get("display_name", "")) == normalized_name
    ]
    best_candidates = exact_matches or candidates

    return max(
        best_candidates,
        key=lambda candidate: (
            candidate.get("cited_by_count") or 0,
            candidate.get("works_count") or 0,
        ),
    )


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

class BibliometrieAgent(BaseAgent):
    """agent responsible for maintaining researcher profiles,
    computing bibliometric metrics, and generating CV PDFs"""

    def __init__(self, name: str, event_bus: EventBus) -> None:
        super().__init__(name, event_bus)             
        self._researchers: Dict[str, Researcher] = {}
        self._load_researchers()  
        self._setup_scholar_proxy()    # sets up proxy on startup        

    def _setup_scholar_proxy(self) -> None:
        # sets up a proxy so Google Scholar doesn't block our requests
        if scholarly is None or ProxyGenerator is None:
            print(f"[{self.name}] Scholar unavailable: {SCHOLARLY_IMPORT_ERROR}")
            return

        api_key = next((os.getenv(name) for name in SCRAPERAPI_KEY_ENV_VARS if os.getenv(name)), None)
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

    def _load_researchers(self) -> None:
        # loads researcher profiles from JSON file if it exists
        if os.path.exists(RESEARCHERS_FILE):
            with open(RESEARCHERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)                    # reads the JSON file
                for name, profile in data.items():
                    self._researchers[name] = Researcher(**profile)
            print(f"[{self.name}] Loaded {len(self._researchers)} researcher profiles")
        else:
            print(f"[{self.name}] No existing profiles found — starting fresh")

    def _save_researchers(self) -> None:
        # saves all researcher profiles to JSON file
        data = {}
        for name, researcher in self._researchers.items():
            # converts each Researcher object to a dictionary for JSON storage
            data[name] = researcher.model_dump(mode="json")
        with open(RESEARCHERS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)   # writes formatted JSON

    def _regenerate_cv(self, researcher: Researcher) -> None:
        os.makedirs("cvs", exist_ok=True)

        filename = researcher.name.replace(" ", "_").lower()
        output_path = f"cvs/{filename}_cv.pdf"

        generate_cv(researcher, output_path)        

    def add_researcher(self, name: str, email: str = None,
                       orcid: str = None, google_scholar_id: str = None) -> Researcher:
        # adds a new researcher to the system
        researcher = Researcher(
            name=name,
            email=email,
            orcid=orcid,
            google_scholar_id=google_scholar_id
        )
        self._researchers[name] = researcher           # stores by name for easy lookup
        self._save_researchers()                       # persists to disk immediately
        print(f"[{self.name}] Added researcher: {name}")
        return researcher

    def get_researcher(self, name: str) -> Researcher | None:
        # returns a researcher by name, or None if not found
        return self._researchers.get(name)

    def list_researchers(self) -> List[Researcher]:
        # returns all researchers in the system
        return list(self._researchers.values())

    def _match_researcher(self, authors: str) -> List[Researcher]:
        # checks if any known researcher appears in a paper's author list
        matched = []
        authors_lower = authors.lower()               
        for name, researcher in self._researchers.items():
            if researcher.name.lower() in authors_lower:
                matched.append(researcher)
        return matched

    def _fetch_semantic_scholar_metrics(self, researcher: Researcher) -> bool:
        try:
            response = requests.get(
                SEMANTIC_SCHOLAR_AUTHOR_SEARCH_URL,
                params={
                    "query": researcher.name,
                    "fields": "name,hIndex,citationCount,paperCount",
                    "limit": 10,
                },
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

        print(
            f"[{self.name}] {researcher.name}: h-index={researcher.h_index}, "
            f"citations={researcher.citation_count} (Semantic Scholar fallback)"
        )
        return True

    def _fetch_openalex_metrics(self, researcher: Researcher) -> bool:
        try:
            response = requests.get(
                OPENALEX_AUTHOR_SEARCH_URL,
                params={"search": researcher.name, "per-page": 10},
                timeout=20,
            )
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

        print(
            f"[{self.name}] {researcher.name}: h-index={researcher.h_index}, "
            f"citations={researcher.citation_count} (OpenAlex fallback)"
        )
        return True

    def _fetch_fallback_metrics(self, researcher: Researcher) -> bool:
        return self._fetch_semantic_scholar_metrics(researcher) or self._fetch_openalex_metrics(researcher)

    def fetch_scholar_metrics(self, researcher: Researcher) -> Researcher:
        if scholarly is None:
            print(f"[{self.name}] Scholar lookup skipped for {researcher.name}: {SCHOLARLY_IMPORT_ERROR}")
            self._fetch_fallback_metrics(researcher)
            return researcher
        
        try:
            print(f"[{self.name}] Searching Google Scholar for: {researcher.name}")

            # searches by name — returns the closest matching profile
            if researcher.google_scholar_id:
                author = scholarly.search_author_id(researcher.google_scholar_id)
            else:
                search_results = scholarly.search_author(researcher.name)
                author = next(search_results, None)    # gets the first result

            if author is None:
                print(f"[{self.name}] No usable Scholar profile found for {researcher.name}; trying fallback sources")
                self._fetch_fallback_metrics(researcher)
                return researcher

            # fetches full profile details including metrics
            author = scholarly.fill(author)

            # updates researcher metrics from Scholar data
            researcher.h_index = author.get("hindex", None)           # h-index
            researcher.citation_count = author.get("citedby", None)   # total citations

            # saves their Google Scholar ID for future lookups
            researcher.google_scholar_id = author.get("scholar_id", researcher.google_scholar_id)

            # updates last_updated timestamp
            researcher.last_updated = datetime.now(timezone.utc)

            print(f"[{self.name}] {researcher.name}: h-index={researcher.h_index}, citations={researcher.citation_count}")

        except Exception as e:
            # if Scholar blocks or fails, log it and continue — don't crash
            print(f"[{self.name}] Scholar lookup failed for {researcher.name}: {type(e).__name__}: {e}")
            self._fetch_fallback_metrics(researcher)

        return researcher

    def update_all_metrics(self) -> None:
        # loops over all researchers and updates their Scholar metrics
        print(f"[{self.name}] Updating metrics for {len(self._researchers)} researchers...")
        for name, researcher in self._researchers.items():
            updated = self.fetch_scholar_metrics(researcher)
            self._researchers[name] = updated    # saves updated profile
        self._save_researchers()                 # persists all changes
        print(f"[{self.name}] Metrics update complete!")
    
    

    async def _handle_article_discovered(self, event: Event) -> None:
        # processes an article.discovered event from the veille agent
        payload = event.payload                        # extracts the event data
        authors = payload.get("authors", "")           # gets the authors string
        matched = self._match_researcher(authors)      # finds matching researchers

        if not matched:
            return                                     # no lab researcher in this paper

        # creates a Publication object from the event payload
        publication = Publication(
            id           = payload.get("paper_id", ""),
            title        = payload.get("title", ""),
            topic        = payload.get("topic", "unknown"),
            source       = payload.get("source", "unknown"),
        )

        for researcher in matched:
            # checks if this publication is already in their list
            existing_ids = [p.id for p in researcher.publications]
            if publication.id in existing_ids:
                continue                              

            researcher.publications.append(publication)

            # updates their topic list if this is a new topic
            if publication.topic not in researcher.topics:
                researcher.topics.append(publication.topic)
            researcher.last_updated = datetime.now(timezone.utc)

            print(f"[{self.name}] Updated {researcher.name}: +1 publication ({publication.title[:50]})")

        self._save_researchers()                      
        for researcher in matched:
            self._regenerate_cv(researcher)                       

    async def on_start(self) -> None:
        # runs when agent starts — subscribes to veille agent's events
        print(f"[{self.name}] Bibliometrie agent starting...")
        # listens for article.discovered events published by veille agent
        await self.event_bus.subscribe(
            "article.discovered",
            self._handle_article_discovered           
        )
        print(f"[{self.name}] Subscribed to article.discovered events")

    async def on_stop(self) -> None:
        print(f"[{self.name}] Bibliometrie agent stopping...")
        self._save_researchers()                      

    async def handle_event(self, event: Event) -> None:
        # generic event handler — routes events to specific handlers
        if event.type == "article.discovered":
            await self._handle_article_discovered(event)

from typing import Optional
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from shared.base_agent import BaseAgent
from shared.schemas import Event, AgentAction, ActionResult
from agents.veille.models import Source, Article, ArticleTag, ArticleSummary
from agents.veille.services.scraper import fetch_rss_feed
from agents.veille.services.arxiv_fetcher import fetch_arxiv
from agents.veille.services.pubmed_fetcher import fetch_pubmed
from agents.veille.services.deduplicator import generate_embedding, is_duplicate, store_embedding
from agents.veille.services.tagger import tag_article
from agents.veille.services.summarizer import summarize_article
import datetime

class VeilleAgent(BaseAgent):
    name = "veille"
    permissions = ["veille.read", "veille.write"]
    requires_human_approval = []

    async def _setup_subscriptions(self):
        """Veille is event-source-only: it does not subscribe, it publishes."""
        pass

    async def handle_event(self, event: Event) -> Optional[AgentAction]:
        """Handle incoming events — e.g. a manual trigger from the orchestrator."""
        return None

    async def execute_action(self, action: AgentAction) -> ActionResult:
        """Execute an approved action."""
        return ActionResult(
            action_id=action.id,
            status="completed",
            result_data={"message": "Action executed by VeilleAgent"}
        )

    # ── Per-source fetch dispatch ────────────────────────────────────────
    #
    # Every fetcher returns a list of dicts with the same shape:
    #   {title, url, abstract, authors, published_at, doi, ...}
    # Source.config (JSON) carries source-specific parameters:
    #   - arxiv:  {"search_query": "all:water stress irrigation", "max_results": 25}
    #   - pubmed: {"term": "water quality", "max_results": 25}
    #   - rss/atom: config is unused; source.url is the feed URL.

    async def _fetch_source(self, source: Source) -> list[dict]:
        """Dispatch to the right fetcher for this source's type."""
        try:
            if source.type in ("rss", "atom"):
                return await fetch_rss_feed(source.url)
            if source.type == "arxiv":
                config = source.config or {}
                query = config.get("search_query") or source.url
                max_results = int(config.get("max_results", 25))
                return await fetch_arxiv(query, max_results=max_results)
            if source.type == "pubmed":
                config = source.config or {}
                term = config.get("term") or source.url
                max_results = int(config.get("max_results", 25))
                return await fetch_pubmed(term, max_results=max_results)
            print(f"[veille] Unknown source type '{source.type}' for '{source.name}' — skipping.")
            return []
        except Exception as e:
            print(f"[veille] Error fetching source '{source.name}' ({source.type}): {e}")
            return []

    async def _ingest_item(
        self, db: AsyncSession, item: dict, source: Source,
    ) -> dict | None:
        """Run one fetched item through embed → dedup → tag → summarize → persist.

        Returns the event payload if the article was stored, or None if it was
        skipped (duplicate, no embedding, etc.).
        """
        text_for_embed = f"{item['title']} {item['abstract'] or ''}"

        embedding = await generate_embedding(text_for_embed)
        if not embedding:
            return None

        if await is_duplicate(db, embedding, threshold=0.1):
            return None

        article = Article(
            title=item['title'],
            abstract=item.get('abstract'),
            url=item.get('url'),
            source_id=source.id,
            published_at=item.get('published_at'),
        )
        await store_embedding(article, embedding)
        db.add(article)
        await db.flush()  # flush to get article.id

        tags = await tag_article(item['title'], item.get('abstract') or "")
        for tag_info in tags:
            db.add(ArticleTag(
                article_id=article.id,
                tag=tag_info.get("tag", "Unknown"),
                confidence=tag_info.get("confidence"),
            ))

        for lang in ["fr", "en"]:
            summary = await summarize_article(item['title'], item.get('abstract') or "", language=lang)
            if summary:
                db.add(ArticleSummary(
                    article_id=article.id,
                    language=lang,
                    summary_text=summary,
                ))

        return {
            "article_id": article.id,
            "title": item['title'],
            "authors": item.get('authors') or [],
            "source": source.name,
            "url": item.get('url'),
            "doi": item.get('doi'),
        }

    async def run_collection(self, db: AsyncSession):
        """Execute a collection run across all active sources.

        Supports rss / atom / arxiv / pubmed source types. After committing new
        articles, emits a veille.article_collected event per article onto the bus,
        which makes the veille → bibliometrie and veille → orchestrateur chains
        real end-to-end.

        We commit after EACH article (not once at the end) for two reasons:
          1. SQLite only allows one writer — holding the write lock across the
             embedding + tagging + summarizing LLM calls (seconds each) makes the
             database effectively unavailable and triggers "database is locked".
          2. The InMemory event bus dispatches handlers synchronously inside the
             publisher's coroutine, and the orchestrator/bibliometrie handlers
             open their own sessions. Those would deadlock on the write lock if we
             held it open. Emitting the event only after the commit avoids that.
        """
        stmt = select(Source).where(Source.active == True)
        result = await db.execute(stmt)
        sources = result.scalars().all()

        for source in sources:
            items = await self._fetch_source(source)
            for item in items:
                payload = await self._ingest_item(db, item, source)
                if payload is None:
                    continue
                source.last_scraped = datetime.datetime.utcnow()
                await db.commit()
                # Emit only after the commit so bus handlers don't contend for the lock.
                await self.emit_event("events", Event(
                    id=str(uuid4()),
                    type="veille.article_collected",
                    source_agent="veille",
                    payload=payload,
                ))
            # Mark last_scraped even when all items were duplicates/skipped.
            source.last_scraped = datetime.datetime.utcnow()
            await db.commit()

veille_agent = VeilleAgent()

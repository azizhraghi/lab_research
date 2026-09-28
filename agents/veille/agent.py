from typing import Optional
import asyncio
import logging
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from shared.base_agent import BaseAgent
from shared.schemas import Event, AgentAction, ActionResult
from agents.veille.models import Source, Article, ArticleTag, ArticleSummary, CollectionRun
from agents.veille.services.scraper import fetch_rss_feed
from agents.veille.services.arxiv_fetcher import fetch_arxiv
from agents.veille.services.pubmed_fetcher import fetch_pubmed
from agents.veille.services.deduplicator import generate_embedding, is_duplicate, store_embedding
from agents.veille.services.tagger import tag_article
from agents.veille.services.summarizer import summarize_article
from agents.veille.services.digests import create_due_digests
import datetime


logger = logging.getLogger("lrste.veille")

class VeilleAgent(BaseAgent):
    name = "veille"
    permissions = ["veille.read", "veille.write"]
    requires_human_approval = []

    def __init__(self):
        super().__init__()
        self._scheduler_task: asyncio.Task | None = None
        self._scheduler_stop = asyncio.Event()

    async def _setup_subscriptions(self):
        """Veille publishes events and owns its single-process collection loop."""
        from shared.config import settings
        if not settings.VEILLE_SCHEDULER_ENABLED:
            logger.info("veille_scheduler_disabled")
            return
        self._scheduler_stop.clear()
        if self._scheduler_task is None or self._scheduler_task.done():
            self._scheduler_task = asyncio.create_task(
                self._collection_scheduler(), name="lrste-veille-scheduler",
            )

    async def _collection_scheduler(self) -> None:
        """Run collection on the configured interval without blocking API requests.

        Production deployments with multiple API replicas should run this job in
        exactly one worker (or use an external scheduler); the database run log
        makes every attempt visible either way.
        """
        from shared.config import settings
        from shared.database import AsyncSessionLocal

        interval = max(1, settings.VEILLE_COLLECTION_INTERVAL_HOURS) * 3600
        while not self._scheduler_stop.is_set():
            try:
                await asyncio.wait_for(self._scheduler_stop.wait(), timeout=interval)
                continue
            except asyncio.TimeoutError:
                pass
            try:
                async with AsyncSessionLocal() as db:
                    await self.run_collection(db, trigger="scheduled")
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("scheduled_collection_failed")

    async def stop(self):
        self._scheduler_stop.set()
        if self._scheduler_task is not None:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
            self._scheduler_task = None
        await super().stop()

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

    async def _fetch_source(self, source: Source) -> tuple[list[dict], str | None]:
        """Dispatch to the right fetcher for this source's type."""
        try:
            if source.type in ("rss", "atom"):
                return await fetch_rss_feed(source.url), None
            if source.type == "arxiv":
                config = source.config or {}
                query = config.get("search_query") or source.url
                max_results = int(config.get("max_results", 25))
                return await fetch_arxiv(query, max_results=max_results), None
            if source.type == "pubmed":
                config = source.config or {}
                term = config.get("term") or source.url
                max_results = int(config.get("max_results", 25))
                return await fetch_pubmed(term, max_results=max_results), None
            print(f"[veille] Unknown source type '{source.type}' for '{source.name}' — skipping.")
            return [], f"{source.name}: unsupported source type '{source.type}'"
        except Exception as e:
            message = f"{source.name} ({source.type}): {type(e).__name__}: {e}"
            logger.exception("veille_source_fetch_failed", extra={"source": source.name, "source_type": source.type})
            return [], message

    async def _ingest_item(
        self, db: AsyncSession, item: dict, source: Source,
    ) -> dict | None:
        """Run one fetched item through embed → dedup → tag → summarize → persist.

        Returns the event payload if the article was stored, or None if it was
        skipped (duplicate, no embedding, etc.).
        """
        doi = str(item.get("doi") or "").strip() or None
        # Embedding similarity catches semantic duplicates across feeds, while
        # DOI is the authoritative publication identifier. Check it first so a
        # differently worded RSS title cannot violate the unique DOI index.
        if doi:
            existing_doi = await db.scalar(select(Article.id).where(Article.doi == doi))
            if existing_doi is not None:
                return None

        text_for_embed = f"{item['title']} {item['abstract'] or ''}"

        embedding = await generate_embedding(text_for_embed)
        if not embedding:
            raise ValueError("Embedding service returned no vector; check Mistral configuration and quota.")

        if await is_duplicate(db, embedding, threshold=0.1):
            return None

        article = Article(
            title=item['title'],
            abstract=item.get('abstract'),
            authors=[str(author).strip() for author in (item.get("authors") or []) if str(author).strip()],
            doi=doi,
            url=item.get('url'),
            source_id=source.id,
            published_at=item.get('published_at'),
        )
        await store_embedding(article, embedding)
        db.add(article)
        await db.flush()  # flush to get article.id

        # Discovery and provenance remain valuable when optional AI enrichment is
        # temporarily unavailable (for example, an upstream rate limit).  Persist
        # the source record and make the incomplete enrichment explicit instead
        # of silently dropping a real publication.
        enrichment_warnings: list[str] = []
        try:
            tags = await tag_article(item['title'], item.get('abstract') or "")
        except RuntimeError as exc:
            tags = [{"tag": "Automated tagging pending", "confidence": None}]
            enrichment_warnings.append(f"automated tagging pending: {exc}")
        for tag_info in tags:
            db.add(ArticleTag(
                article_id=article.id,
                tag=tag_info.get("tag", "Unknown"),
                confidence=tag_info.get("confidence"),
            ))

        # A missing generated summary is also visible in the collection warning;
        # the source abstract is retained as the reviewable primary text.
        for lang in ["fr", "en"]:
            try:
                summary = await summarize_article(item['title'], item.get('abstract') or "", language=lang)
            except RuntimeError as exc:
                enrichment_warnings.append(f"{lang} summary pending: {exc}")
                continue
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
            "enrichment_warnings": enrichment_warnings,
        }

    async def run_collection(self, db: AsyncSession, trigger: str = "manual") -> CollectionRun:
        """Execute a collection run across all active sources.

        Supports rss / atom / arxiv / pubmed source types. After committing new
        articles, emits a veille.article_collected event per article onto the bus,
        which makes the veille → bibliometrie and veille → orchestrateur chains
        real end-to-end.

        We commit after EACH article (not once at the end) for two reasons:
          1. SQLite only allows one writer — holding the write lock across the
             embedding + tagging + summarizing LLM calls (seconds each) makes the
             database effectively unavailable and triggers "database is locked".
          2. Bus handlers (orchestrateur, bibliometrie, …) open their own
             sessions. Even with the bus's background dispatch worker, emitting
             only after the commit guarantees a handler never waits on a write
             lock this coroutine still holds.
        """
        run = CollectionRun(trigger=trigger, status="running")
        db.add(run)
        await db.commit()
        await db.refresh(run)
        # A failed transaction expires ORM attributes, so preserve the primary
        # key before work begins for reliable failure reporting below.
        run_id = run.id
        try:
            stmt = select(Source).where(Source.active == True)
            result = await db.execute(stmt)
            sources = result.scalars().all()
            run.source_count = len(sources)
            articles_collected = 0
            warnings: list[str] = []
            successful_sources = 0
            # Dispatch only after this collection has released its SQLite write
            # transaction.  In-memory event consumers may write audit records,
            # and dispatching between per-article commits can otherwise contend
            # with the next source update in a local demo database.
            pending_events: list[Event] = []

            for source in sources:
                items, warning = await self._fetch_source(source)
                if warning:
                    warnings.append(warning)
                    continue
                successful_sources += 1
                for item in items:
                    try:
                        # A failed enrichment does not roll back other articles.
                        async with db.begin_nested():
                            payload = await self._ingest_item(db, item, source)
                    except Exception as exc:
                        warnings.append(f"{source.name}: {item.get('title', 'Article')[:100]}: {type(exc).__name__}: {exc}")
                        continue
                    if payload is None:
                        continue
                    for enrichment_warning in payload.get("enrichment_warnings", []):
                        warnings.append(
                            f"{source.name}: {item.get('title', 'Article')[:100]}: {enrichment_warning}"
                        )
                    source.last_scraped = datetime.datetime.utcnow()
                    run.articles_collected = articles_collected = articles_collected + 1
                    await db.commit()
                    pending_events.append(Event(
                        id=str(uuid4()),
                        type="veille.article_collected",
                        source_agent="veille",
                        payload=payload,
                    ))
                # Mark last_scraped even when all items were duplicates/skipped.
                source.last_scraped = datetime.datetime.utcnow()
                await db.commit()

            run.digests_created = await create_due_digests(db)
            run.status = ("failed" if sources and successful_sources == 0
                          else "completed_with_warnings" if warnings else "completed")
            run.error_message = "\n".join(warnings)[:2000] or None
            run.completed_at = datetime.datetime.utcnow()
            await db.commit()
            await db.refresh(run)
            for event in pending_events:
                try:
                    await self.emit_event("events", event)
                except Exception as exc:
                    # The literature is already durably collected.  Keep a
                    # visible recovery signal without presenting it as a failed
                    # source fetch or deleting the publication.
                    warnings.append(f"event delivery pending: {type(exc).__name__}: {exc}")
            return run
        except Exception as exc:
            await db.rollback()
            failed_run = await db.get(CollectionRun, run_id)
            if failed_run is not None:
                failed_run.status = "failed"
                failed_run.error_message = f"{type(exc).__name__}: {exc}"[:2000]
                failed_run.completed_at = datetime.datetime.utcnow()
                await db.commit()
            raise

veille_agent = VeilleAgent()

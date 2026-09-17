"""Matching and creation of durable, in-app scientific-watch digests."""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from agents.veille.models import AlertRule, Article, WatchDigest, WatchDigestItem


def article_matches_rule(article: Article, rule: AlertRule) -> bool:
    """Match a subscription without using an opaque relevance score.

    Keywords search the title, abstract, DOI and author list; themes match the
    agent-assigned tags. An empty subscription means "all collected literature",
    which is useful for a lab director's broad daily inbox.
    """
    keywords = [term.casefold() for term in (rule.keywords or []) if term]
    themes = [term.casefold() for term in (rule.themes or []) if term]
    if not keywords and not themes:
        return True

    text = " ".join([
        article.title or "", article.abstract or "", article.doi or "",
        " ".join(article.authors or []),
    ]).casefold()
    tag_set = {tag.tag.casefold() for tag in article.tags if tag.tag}
    return any(term in text for term in keywords) or any(theme in tag_set for theme in themes)


async def create_due_digests(db: AsyncSession, now: datetime | None = None) -> int:
    """Create one immutable in-app digest for each due active subscription.

    A digest is created only when matching articles appeared since its previous
    cutoff. We still advance the cutoff on an empty period, which avoids an old
    article suddenly appearing weeks later when a researcher broadens a theme.
    """
    now = now or datetime.utcnow()
    rules = (await db.execute(
        select(AlertRule)
        .where(AlertRule.active.is_(True))
        .options(selectinload(AlertRule.notifications))
    )).scalars().all()
    created = 0

    for rule in rules:
        interval = timedelta(days=7 if rule.frequency == "weekly" else 1)
        cutoff = rule.last_digest_at or rule.created_at or now
        if now < cutoff + interval:
            continue

        articles = (await db.execute(
            select(Article)
            .where(Article.collected_at > cutoff, Article.collected_at <= now)
            .options(selectinload(Article.tags), selectinload(Article.summaries))
            .order_by(Article.published_at.desc(), Article.id.desc())
        )).scalars().all()
        matches = [article for article in articles if article_matches_rule(article, rule)]
        if matches:
            digest = WatchDigest(
                rule_id=rule.id, user_id=rule.user_id, frequency=rule.frequency,
                period_start=cutoff, period_end=now, item_count=len(matches),
            )
            db.add(digest)
            await db.flush()
            for article in matches:
                db.add(WatchDigestItem(digest_id=digest.id, article_id=article.id))
            created += 1
        rule.last_digest_at = now

    return created

"""Scientific-watch API: collection, personal subscriptions, and review inbox."""
from __future__ import annotations

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from shared.database import get_db
from shared.security import User, get_current_user, require_roles
from agents.veille.models import (
    AlertRule, Article, ArticleUserState, CollectionRun, Source,
    WatchDigest, WatchDigestItem,
)
from agents.veille.schemas import (
    AlertRuleCreate, AlertRuleResponse, AlertRuleUpdate, ArticleResponse,
    ArticleStateUpdate, ArticleUserStateSchema, CollectionRunResponse,
    DigestItemResponse, SourceCreate, SourceDeleteResponse, SourceResponse,
    WatchDigestResponse,
)


router = APIRouter()


def _state_schema(state: ArticleUserState | None) -> dict:
    return {
        "is_saved": bool(state and state.is_saved),
        "read_at": state.read_at if state else None,
        "shared_at": state.shared_at if state else None,
        "share_note": state.share_note if state else None,
    }


def _article_response(article: Article, state: ArticleUserState | None = None) -> dict:
    response = ArticleResponse.model_validate(article).model_dump()
    response["state"] = _state_schema(state)
    return response


async def _states_for_articles(
    db: AsyncSession, user_id: str, article_ids: list[int],
) -> dict[int, ArticleUserState]:
    if not article_ids:
        return {}
    rows = (await db.execute(
        select(ArticleUserState).where(
            ArticleUserState.user_id == user_id,
            ArticleUserState.article_id.in_(article_ids),
        )
    )).scalars().all()
    return {row.article_id: row for row in rows}


async def _owned_rule(db: AsyncSession, rule_id: int, user_id: str) -> AlertRule:
    rule = await db.get(AlertRule, rule_id)
    if rule is None or rule.user_id != user_id:
        raise HTTPException(status_code=404, detail="Watch subscription not found")
    return rule


@router.get("/articles", response_model=List[ArticleResponse])
async def list_articles(
    search: str = Query("", max_length=200),
    tag: str | None = Query(None, max_length=100),
    state: str = Query("all", pattern="^(all|unread|read|saved|shared)$"),
    limit: int = Query(100, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search collected literature and return the caller's persisted state."""
    articles = (await db.execute(
        select(Article)
        .options(selectinload(Article.tags), selectinload(Article.summaries))
        .order_by(Article.published_at.desc(), Article.collected_at.desc())
        .limit(200)
    )).scalars().all()
    needle = search.casefold().strip()
    tag_needle = tag.casefold().strip() if tag else ""
    if needle:
        articles = [article for article in articles if needle in " ".join([
            article.title or "", article.abstract or "", article.doi or "",
            " ".join(article.authors or []), " ".join(t.tag or "" for t in article.tags),
        ]).casefold()]
    if tag_needle:
        articles = [article for article in articles if any(t.tag.casefold() == tag_needle for t in article.tags if t.tag)]

    states = await _states_for_articles(db, user.id, [article.id for article in articles])
    def matches_state(article: Article) -> bool:
        article_state = states.get(article.id)
        if state == "unread":
            return article_state is None or article_state.read_at is None
        if state == "read":
            return bool(article_state and article_state.read_at)
        if state == "saved":
            return bool(article_state and article_state.is_saved)
        if state == "shared":
            return bool(article_state and article_state.shared_at)
        return True
    return [_article_response(article, states.get(article.id)) for article in articles if matches_state(article)][:limit]


@router.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    article = (await db.execute(
        select(Article).options(selectinload(Article.tags), selectinload(Article.summaries))
        .where(Article.id == article_id)
    )).scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    state = await db.scalar(select(ArticleUserState).where(
        ArticleUserState.user_id == user.id, ArticleUserState.article_id == article_id,
    ))
    return _article_response(article, state)


@router.patch("/articles/{article_id}/state", response_model=ArticleResponse)
async def update_article_state(
    article_id: int,
    data: ArticleStateUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    article = (await db.execute(
        select(Article).options(selectinload(Article.tags), selectinload(Article.summaries))
        .where(Article.id == article_id)
    )).scalar_one_or_none()
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    state = await db.scalar(select(ArticleUserState).where(
        ArticleUserState.user_id == user.id, ArticleUserState.article_id == article_id,
    ))
    if state is None:
        state = ArticleUserState(user_id=user.id, article_id=article_id)
        db.add(state)
    now = datetime.utcnow()
    if data.is_saved is not None:
        state.is_saved = data.is_saved
    if data.mark_read is not None:
        state.read_at = now if data.mark_read else None
    if data.mark_shared is not None:
        state.shared_at = now if data.mark_shared else None
    if data.share_note is not None:
        state.share_note = data.share_note
        if data.share_note and state.shared_at is None:
            state.shared_at = now
    await db.commit()
    await db.refresh(state)
    return _article_response(article, state)


@router.get("/subscriptions", response_model=list[AlertRuleResponse])
async def list_subscriptions(
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    return (await db.execute(
        select(AlertRule).where(AlertRule.user_id == user.id).order_by(AlertRule.created_at.desc())
    )).scalars().all()


@router.post(
    "/subscriptions", response_model=AlertRuleResponse,
    dependencies=[Depends(require_roles("researcher", "reviewer", "administrator"))],
)
async def create_subscription(
    data: AlertRuleCreate,
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    rule = AlertRule(user_id=user.id, **data.model_dump(), delivery_channel="in_app")
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.patch(
    "/subscriptions/{rule_id}", response_model=AlertRuleResponse,
    dependencies=[Depends(require_roles("researcher", "reviewer", "administrator"))],
)
async def update_subscription(
    rule_id: int, data: AlertRuleUpdate,
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    rule = await _owned_rule(db, rule_id, user.id)
    for name, value in data.model_dump(exclude_unset=True).items():
        if name in {"keywords", "themes"} and value is not None:
            value = list(dict.fromkeys(term.strip() for term in value if term and term.strip()))
        setattr(rule, name, value)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.delete(
    "/subscriptions/{rule_id}", status_code=204,
    dependencies=[Depends(require_roles("researcher", "reviewer", "administrator"))],
)
async def delete_subscription(
    rule_id: int, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    rule = await _owned_rule(db, rule_id, user.id)
    await db.delete(rule)
    await db.commit()


@router.get("/inbox", response_model=list[WatchDigestResponse])
async def list_inbox(
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    digests = (await db.execute(
        select(WatchDigest)
        .where(WatchDigest.user_id == user.id)
        .options(
            selectinload(WatchDigest.items).selectinload(WatchDigestItem.article).selectinload(Article.tags),
            selectinload(WatchDigest.items).selectinload(WatchDigestItem.article).selectinload(Article.summaries),
        )
        .order_by(WatchDigest.created_at.desc()).limit(limit)
    )).scalars().all()
    article_ids = [item.article_id for digest in digests for item in digest.items]
    states = await _states_for_articles(db, user.id, article_ids)
    return [{
        "id": digest.id, "rule_id": digest.rule_id, "user_id": digest.user_id,
        "frequency": digest.frequency, "period_start": digest.period_start,
        "period_end": digest.period_end, "item_count": digest.item_count,
        "created_at": digest.created_at,
        "items": [{"article": _article_response(item.article, states.get(item.article_id))} for item in digest.items],
    } for digest in digests]


@router.get("/runs", response_model=list[CollectionRunResponse])
async def list_collection_runs(
    limit: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db),
):
    return (await db.execute(
        select(CollectionRun).order_by(CollectionRun.started_at.desc()).limit(limit)
    )).scalars().all()


@router.post("/sources", response_model=SourceResponse, dependencies=[Depends(require_roles("researcher", "reviewer", "administrator"))])
async def add_source(source: SourceCreate, db: AsyncSession = Depends(get_db)):
    db_source = Source(**source.model_dump())
    db.add(db_source)
    await db.commit()
    await db.refresh(db_source)
    return db_source


@router.get("/sources", response_model=List[SourceResponse])
async def list_sources(db: AsyncSession = Depends(get_db)):
    return (await db.execute(select(Source))).scalars().all()


@router.delete(
    "/sources/{source_id}", response_model=SourceDeleteResponse,
    dependencies=[Depends(require_roles("reviewer", "administrator"))],
)
async def delete_source(source_id: int, db: AsyncSession = Depends(get_db)):
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail=f"Source {source_id} not found")
    article_count = await db.scalar(select(func.count()).select_from(Article).where(Article.source_id == source_id))
    if article_count:
        raise HTTPException(
            status_code=409,
            detail=f"Source '{source.name}' still has {article_count} collected articles. Delete or archive them separately.",
        )
    name, source_type = source.name, source.type
    await db.delete(source)
    await db.commit()
    return SourceDeleteResponse(deleted_id=source_id, name=name, type=source_type)


@router.post("/trigger", response_model=CollectionRunResponse, dependencies=[Depends(require_roles("researcher", "reviewer", "administrator"))])
async def trigger_collection(db: AsyncSession = Depends(get_db)):
    """Run collection now; the same workflow runs automatically on its cadence."""
    try:
        from agents.veille.agent import veille_agent
        return await veille_agent.run_collection(db, trigger="manual")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

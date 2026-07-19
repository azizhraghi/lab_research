from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List

from shared.database import get_db
from shared.security import require_roles
from agents.veille.models import Article, Source, AlertRule
from agents.veille.schemas import ArticleResponse, SourceResponse, SourceCreate

router = APIRouter()

@router.get("/articles", response_model=List[ArticleResponse])
async def list_articles(db: AsyncSession = Depends(get_db)):
    stmt = select(Article).options(
        selectinload(Article.tags), 
        selectinload(Article.summaries)
    ).order_by(Article.published_at.desc()).limit(50)
    
    result = await db.execute(stmt)
    articles = result.scalars().all()
    return articles

@router.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Article).options(
        selectinload(Article.tags), 
        selectinload(Article.summaries)
    ).where(Article.id == article_id)
    
    result = await db.execute(stmt)
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article

@router.post("/sources", response_model=SourceResponse, dependencies=[Depends(require_roles("researcher", "reviewer", "administrator"))])
async def add_source(source: SourceCreate, db: AsyncSession = Depends(get_db)):
    """Add an RSS source. No auth required for dev testing."""
    db_source = Source(**source.model_dump())
    db.add(db_source)
    await db.commit()
    await db.refresh(db_source)
    return db_source

@router.get("/sources", response_model=List[SourceResponse])
async def list_sources(db: AsyncSession = Depends(get_db)):
    """List all configured sources."""
    stmt = select(Source)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/trigger", dependencies=[Depends(require_roles("researcher", "reviewer", "administrator"))])
async def trigger_collection(db: AsyncSession = Depends(get_db)):
    """Trigger article collection. Runs synchronously (no Celery needed)."""
    try:
        from agents.veille.agent import veille_agent
        await veille_agent.run_collection(db)
        return {"status": "Collection completed successfully"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

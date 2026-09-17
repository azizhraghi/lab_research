"""Private literature screening based on captured PubMed abstract evidence."""
from datetime import datetime
import re
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.veille.models import LiteratureReview
from agents.veille.services.pubmed_fetcher import fetch_pubmed
from agents.bibliometrie.services.orcid_sync import normalise_doi
from shared.database import get_db
from shared.security import User, get_current_user, require_roles

router = APIRouter()
writer = Depends(require_roles("researcher", "reviewer", "administrator"))

class ReviewCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    topic: str = Field(min_length=3, max_length=200)
    max_results: int = Field(default=10, ge=1, le=20)

class Decision(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    decision: Literal["pending", "include", "exclude"]
    note: str = Field(default="", max_length=5000)


def evidence_items(topic, records):
    tokens = [t for t in re.findall(r"[\w-]+",topic.casefold()) if len(t)>2 and t not in {"and","the","for","not","with","from"}]
    result, seen = [], set()
    for record in records:
        doi = normalise_doi(record["doi"]) if record.get("doi") else None
        key = doi or record["url"]
        if key in seen: continue
        seen.add(key)
        text = (record["title"]+" "+(record.get("abstract") or "")).casefold()
        matched = list(dict.fromkeys(token for token in tokens if token in text))
        abstract = record.get("abstract")
        result.append(dict(id=str(uuid4()), title=record["title"], authors=record.get("authors",[]), doi=doi,
            url=record["url"], published_at=record["published_at"].isoformat() if record.get("published_at") else None,
            abstract=abstract, evidence_basis="abstract only" if abstract else "metadata only",
            evidence_excerpt=(abstract[:900] + ("…" if len(abstract)>900 else "")) if abstract else None,
            relevance="Literal topic terms in title/abstract: " + ", ".join(matched) if matched else "Returned by PubMed query expansion; no literal topic-term match. Review relevance manually.",
            decision="pending", note="", reviewed_at=None))
    return result


async def owned(db, review_id, user, lock=False):
    query=select(LiteratureReview).where(LiteratureReview.id==review_id,LiteratureReview.user_id==user.id)
    if lock: query=query.with_for_update()
    review=await db.scalar(query)
    if review is None: raise HTTPException(404,"Literature review not found")
    return review


def response(review):
    return dict(id=review.id,topic=review.topic,status=review.status,error_message=review.error_message,
                items=review.items,created_at=review.created_at,updated_at=review.updated_at)


@router.get("/reviews")
async def list_reviews(user: User=Depends(get_current_user),db: AsyncSession=Depends(get_db)):
    rows=(await db.execute(select(LiteratureReview).where(LiteratureReview.user_id==user.id)
        .order_by(LiteratureReview.created_at.desc()).limit(50))).scalars().all()
    return [response(row) for row in rows]


@router.post("/reviews")
async def collect_review(data: ReviewCreate,user: User=writer,db: AsyncSession=Depends(get_db)):
    review=LiteratureReview(id=str(uuid4()),user_id=user.id,topic=data.topic,items=[],status="collecting")
    db.add(review)
    await db.commit()
    try:
        records=await fetch_pubmed(data.topic,max_results=data.max_results)
        review.items=evidence_items(data.topic,records)
        review.status="ready"
    except Exception as exc:
        review.status="failed"
        review.error_message=f"{type(exc).__name__}: {exc}"[:2000]
    await db.commit()
    await db.refresh(review)
    return response(review)


@router.patch("/reviews/{review_id}/items/{item_id}")
async def decide(review_id: str,item_id: str,data: Decision,user: User=writer,db: AsyncSession=Depends(get_db)):
    review=await owned(db,review_id,user,lock=True)
    items=[dict(item) for item in review.items]
    item=next((item for item in items if item["id"]==item_id),None)
    if item is None: raise HTTPException(404,"Review item not found")
    item.update(decision=data.decision,note=data.note,reviewed_at=datetime.utcnow().isoformat())
    review.items=items
    await db.commit()
    await db.refresh(review)
    return response(review)


@router.get("/reviews/{review_id}/export")
async def export_review(review_id: str,user: User=Depends(get_current_user),db: AsyncSession=Depends(get_db)):
    review=await owned(db,review_id,user)
    included=[item for item in review.items if item["decision"]=="include"]
    if not included: raise HTTPException(409,"Include at least one paper before exporting.")
    lines=["ANNOTATED BIBLIOGRAPHY",review.topic,f"Collected: {review.created_at.isoformat()} UTC",
           "Source: PubMed. Abstract evidence only; no full-text or scientific-quality assessment.",
           "Inclusion is the current user's screening decision, not laboratory approval.",""]
    for number,item in enumerate(included,1):
        lines.extend([f"{number}. {item['title']}","Authors: "+", ".join(item["authors"]),
            "Publication date (may be approximate): "+str(item["published_at"] or "unknown"),
            "Source: "+item["url"],"DOI: "+str(item["doi"] or "not supplied"),
            "Relevance: "+item["relevance"],"Evidence: "+item["evidence_basis"],
            "Source abstract excerpt: "+str(item["evidence_excerpt"] or "No abstract available; consult the original publication."),
            "Reviewer note: "+(item["note"] or "No annotation entered."),""])
    return dict(filename=f"literature-review-{review.id}.txt",content="\n".join(lines),item_count=len(included))

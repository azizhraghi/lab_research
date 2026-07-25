# -*- coding: utf-8 -*-

from __future__ import annotations                    
import sys
import os



# builds the absolute path to veille-agent folder regardless of where the script runs from
_veille_path = r"C:\Users\IO\veille-agent\venv"
if _veille_path not in sys.path:
    sys.path.insert(0, _veille_path)

from app.core.base_agent import BaseAgent             
from app.core.event_bus import EventBus               
from app.schemas.events import Event                  
from app.schemas.veille import ArticleDiscoveredPayload  

# imports our existing pipeline functions from veille-agent folder
from fetch import fetch_papers                        # arXiv fetcher
from fetchpubmed import fetch_pubmed                  # PubMed fetcher
from database import Paper, get_engine, init_db       # our local database
from sqlalchemy.orm import Session                    # database session
from config import TOPICS                             # lab topic list
import math                                           
import asyncio                                      

def cosine_similarity(vec1, vec2):
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))
    return dot_product / (magnitude1 * magnitude2)

def is_duplicate(new_embedding, session, threshold=0.92):
    existing = session.query(Paper).filter(Paper.embedding != None).all()
    for paper in existing:
        if cosine_similarity(new_embedding, paper.embedding) > threshold:
            return True
    return False

def save_papers(papers, session):
    newly_saved = []                                 
    for paper in papers:
        existing = session.get(Paper, paper.id)
        if existing:
            continue                                  

        if is_duplicate(paper.embedding, session):
            continue                                  

        session.add(paper)                            
        newly_saved.append(paper)                    

    session.commit()                                  
    return newly_saved                                

class VeilleAgent(BaseAgent):
    """agent responsible for fetching, deduplicating, classifying
    and summarizing scientific papers, then publishing discovery events"""

    def __init__(self, name: str, event_bus: EventBus) -> None:
        super().__init__(name, event_bus)             # calls BaseAgent's constructor
        self.engine = get_engine()                    # connects to local SQLite database
        init_db(self.engine)                          # creates tables if they don't exist

    async def on_start(self) -> None:
        print(f"[{self.name}] Veille agent starting...")
        await self.run_pipeline()                     # runs the full fetch pipeline on startup

    async def on_stop(self) -> None:
        print(f"[{self.name}] Veille agent stopping...")

    async def handle_event(self, event: Event) -> None:
        print(f"[{self.name}] received event: {event.type}")

    async def run_pipeline(self) -> None:
        print(f"[{self.name}] Starting pipeline for {len(TOPICS)} topics...")

        for topic in TOPICS:
            print(f"[{self.name}] Fetching arXiv: {topic}")
            arxiv_papers = fetch_papers(topic, max_results=3)    # fetches from arXiv
            await self._process_and_publish(arxiv_papers)        # saves + publishes events

            
            print(f"[{self.name}] Fetching PubMed: {topic}")
            pubmed_papers = fetch_pubmed(topic, max_results=3)   # fetches from PubMed
            await self._process_and_publish(pubmed_papers)       # saves + publishes events

        print(f"[{self.name}] Pipeline complete.")

    async def _process_and_publish(self, papers) -> None:
        # saves papers to DB then publishes an event for each new one
        with Session(self.engine) as session:
            newly_saved = save_papers(papers, session)    

            for paper in newly_saved:
                payload = ArticleDiscoveredPayload(
    paper_id     = paper.id,
    title        = paper.title,
    authors      = paper.authors or "",
    topic        = paper.topic or "unknown",
    plain_summary= paper.plain_summary or "",
    source       = "pubmed" if paper.id.startswith("pubmed:") else "arxiv",
    discovered_at= str(paper.id),
)

                
                event = Event(
                    type         = "article.discovered",    
                    source_agent = self.name,               
                    payload      = payload.model_dump(),    
                )

                
                await self.event_bus.publish("article.discovered", event)
                print(f"[{self.name}] Published: {paper.title[:60]}")
# main.py — the single entry point for your entire agent
# running this file triggers the full pipeline: arXiv + PubMed, all topics

import time                          # for pausing between sources to respect rate limits
from fetch import fetch_papers       # arXiv fetching function
from fetchpubmed import fetch_pubmed    # PubMed fetching function
from database import Paper, get_engine, init_db    # database setup
from sqlalchemy.orm import Session   # database session
from config import TOPICS            # the lab's topic list
import math                          # for cosine similarity
from app.core.event_bus import InMemoryEventBus
from app.schemas.events import Event


def cosine_similarity(vec1, vec2):
    # compares two vectors — returns a score between 0 (unrelated) and 1 (identical)
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))
    return dot_product / (magnitude1 * magnitude2)

def is_duplicate(new_embedding, session, threshold=0.92):
    # checks if a new paper is semantically too similar to an existing one
    existing_papers = session.query(Paper).filter(Paper.embedding != None).all()
    for paper in existing_papers:
        if cosine_similarity(new_embedding, paper.embedding) > threshold:
            return True
    return False

def save_papers(papers, session):
    saved = 0
    skipped = 0
    newly_saved = []          # <-- NEW: track what we actually saved

    for paper in papers:
        existing = session.get(Paper, paper.id)
        if existing:
            skipped += 1
            continue

        if is_duplicate(paper.embedding, session):
            skipped += 1
            continue

        session.add(paper)
        saved += 1
        newly_saved.append(paper)   # <-- NEW

    session.commit()
    return saved, skipped, newly_saved   # <-- NEW: one extra return value

def run():
    print("🚀 Starting Veille Scientifique Agent")
    print(f"   Monitoring {len(TOPICS)} topics across 2 sources\n")

    engine = get_engine()     # connects to the database
    init_db(engine)           # creates tables if they don't exist

    total_saved = 0
    total_skipped = 0

    # --- arXiv ---
    print("📚 Source 1: arXiv")
    for topic in TOPICS:
        print(f"\n  🔍 Topic: {topic}")
        papers = fetch_papers(topic, max_results=3)    # fetches 3 papers per topic

        with Session(engine) as session:
            saved, skipped = save_papers(papers, session)
            total_saved += saved
            total_skipped += skipped
            print(f"  ✅ Saved: {saved} | Skipped: {skipped}")

        time.sleep(2)    # pause between topics to avoid rate limits

    # --- PubMed ---
    print("\n📚 Source 2: PubMed")
    for topic in TOPICS:
        print(f"\n  🔍 Topic: {topic}")
        papers = fetch_pubmed(topic, max_results=3)    # fetches 3 papers per topic

        with Session(engine) as session:
            saved, skipped = save_papers(papers, session)
            total_saved += saved
            total_skipped += skipped
            print(f"  ✅ Saved: {saved} | Skipped: {skipped}")

        time.sleep(2)    # pause between topics

    # --- final summary ---
    print(f"\n✅ Agent run complete!")
    print(f"   Total saved: {total_saved}")
    print(f"   Total skipped (duplicates): {total_skipped}")

    with Session(engine) as session:
        total = session.query(Paper).count()
        print(f"   Total papers in DB: {total}")

# this ensures run() only executes when you run this file directly
# not when another file imports from it
if __name__ == "__main__":
    run()
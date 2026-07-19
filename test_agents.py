import asyncio
from shared.database import AsyncSessionLocal
from agents.veille.models import Source
from agents.bibliometrie.models import Researcher
from agents.veille.agent import veille_agent
from agents.bibliometrie.agent import bibliometrie_agent

async def main():
    print("Injecting Test Data for AI Lab (Digital Twins & Hydrology)...")
    
    async with AsyncSessionLocal() as db:
        # --- 1. Test Veille (Hydrology & Digital Twins) ---
        print("\nAdding ArXiv RSS Source for Hydrology...")
        # Add an ArXiv query for hydrology and digital twins
        source = Source(
            name="ArXiv Hydrology & Digital Twins",
            type="rss",
            url="http://export.arxiv.org/api/query?search_query=all:hydrology+AND+all:twin&start=0&max_results=3"
        )
        db.add(source)
        await db.commit()
        
        print("Running Veille Agent (Downloading & Summarizing with Mistral AI)...")
        # Run collection directly (bypassing Celery)
        await veille_agent.run_collection(db)
        print("Veille Agent finished processing articles.")
        
        # --- 2. Test Bibliométrie ---
        print("\nAdding Test Researcher Profile...")
        # Using Albert Einstein's Scholar ID as a guaranteed fallback for testing, 
        # or we could use a known hydrologist if we had their ID. 
        # ID: qc6CJjYAAAAJ (Albert Einstein)
        researcher = Researcher(
            first_name="Albert",
            last_name="Einstein (Test Profile)",
            email="test@lab.org",
            scholar_id="qc6CJjYAAAAJ",
            department="Hydrology & Twins"
        )
        db.add(researcher)
        await db.commit()
        await db.refresh(researcher)
        
        # print(f"Running Bibliometrie Agent for {researcher.first_name}...")
        # # Run sync directly (bypassing Celery)
        # await bibliometrie_agent.run_sync_for_researcher(db, researcher.id)
        # print("Bibliometrie Agent finished calculating metrics and generating CV.")
        
    print("\nTest Data Injection Complete! Check your React Dashboard!")

if __name__ == "__main__":
    asyncio.run(main())

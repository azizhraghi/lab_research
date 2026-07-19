import asyncio
from celery import shared_task
from shared.database import AsyncSessionLocal
from agents.bibliometrie.agent import bibliometrie_agent

@shared_task
def run_researcher_sync_task(researcher_id: int):
    """Run bibliometric sync for a specific researcher."""
    async def _run():
        async with AsyncSessionLocal() as db:
            await bibliometrie_agent.run_sync_for_researcher(db, researcher_id)
            
    asyncio.run(_run())

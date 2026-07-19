import asyncio
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from shared.base_agent import BaseAgent
from shared.schemas import Event, AgentAction, ActionResult
from agents.bibliometrie.models import Researcher, Publication, ResearcherPublication, BiblioIndicator, CVProfile
from agents.bibliometrie.services.orcid_sync import fetch_orcid_works
from agents.bibliometrie.services.scholar_sync import fetch_scholar_works
from agents.bibliometrie.services.indicators import compute_all_indicators

class BibliometrieAgent(BaseAgent):
    name = "bibliometrie"
    permissions = ["biblio.read", "biblio.write"]
    requires_human_approval = ["biblio.update_cv_profile"]

    async def _setup_subscriptions(self):
        pass

    async def handle_event(self, event: Event) -> Optional[AgentAction]:
        return None

    async def execute_action(self, action: AgentAction) -> ActionResult:
        return ActionResult(
            action_id=action.id,
            status="completed",
            result_data={"message": "Action executed by BibliometrieAgent"}
        )
        
    async def run_sync_for_researcher(self, db: AsyncSession, researcher_id: int):
        """Run full sync for a specific researcher."""
        # 1. Fetch researcher
        stmt = select(Researcher).where(Researcher.id == researcher_id)
        result = await db.execute(stmt)
        researcher = result.scalar_one_or_none()
        
        if not researcher:
            return
            
        all_works = []
        
        # 2. Sync ORCID
        if researcher.orcid_id:
            orcid_works = await fetch_orcid_works(researcher.orcid_id)
            all_works.extend(orcid_works)
            
        # 3. Sync Scholar
        if researcher.scholar_id:
            scholar_works = await fetch_scholar_works(researcher.scholar_id)
            all_works.extend(scholar_works)
            
        # 4. Merge and save publications
        for work_data in all_works:
            pub_stmt = select(Publication).where(Publication.title == work_data["title"])
            pub_res = await db.execute(pub_stmt)
            existing_pub = pub_res.scalar_one_or_none()
            
            if not existing_pub:
                pub = Publication(
                    title=work_data["title"],
                    year=work_data.get("year"),
                    type=work_data.get("type"),
                    journal=work_data.get("journal"),
                    doi=work_data.get("doi"),
                    citation_count=work_data.get("citation_count", 0),
                    source=work_data["source"]
                )
                db.add(pub)
                await db.flush()
                
                link = ResearcherPublication(
                    researcher_id=researcher.id,
                    publication_id=pub.id
                )
                db.add(link)
            else:
                if work_data.get("citation_count", 0) > existing_pub.citation_count:
                    existing_pub.citation_count = work_data["citation_count"]
                    
        # 5. Compute indicators
        await db.flush()
        
        cit_stmt = select(Publication.citation_count).join(ResearcherPublication).where(ResearcherPublication.researcher_id == researcher.id)
        cit_res = await db.execute(cit_stmt)
        citations = [c for c in cit_res.scalars().all() if c]
        
        indicators = compute_all_indicators(citations)
        
        for metric, value in indicators.items():
            ind_stmt = select(BiblioIndicator).where(
                BiblioIndicator.researcher_id == researcher.id,
                BiblioIndicator.metric_name == metric
            )
            ind_res = await db.execute(ind_stmt)
            existing_ind = ind_res.scalar_one_or_none()
            
            if existing_ind:
                existing_ind.value = value
            else:
                ind = BiblioIndicator(
                    researcher_id=researcher.id,
                    metric_name=metric,
                    value=value
                )
                db.add(ind)
                
        await db.commit()

bibliometrie_agent = BibliometrieAgent()

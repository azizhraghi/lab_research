import asyncio
from app.core.event_bus import InMemoryEventBus
from app.agents.bibliometrie_agent import BibliometrieAgent
from app.agents.veille_agent import VeilleAgent

async def main():
    bus = InMemoryEventBus()

    
    biblio = BibliometrieAgent(name="bibliometrie", event_bus=bus)
    veille = VeilleAgent(name="veille", event_bus=bus)

    
    biblio.add_researcher("yosr yassoura", email="yosr@lab.com")
  

    print(f"\nResearchers in system: {len(biblio.list_researchers())}")
    for r in biblio.list_researchers():
        print(f"  - {r.name}: {len(r.publications)} publications")
    await biblio.start()
    await veille.start()

    print(f"\nAfter pipeline:")
    for r in biblio.list_researchers():
        print(f"  - {r.name}: {len(r.publications)} publications, topics: {r.topics}")

    await veille.stop()
    await biblio.stop()

asyncio.run(main())
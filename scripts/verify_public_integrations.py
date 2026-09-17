"""Opt-in live smoke check. Writes only a temporary DB and chosen evidence directory.
Run: python scripts/verify_public_integrations.py
Uses a public ORCID example, never registers it in the laboratory database.
"""
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
ORCID = "0000-0003-1315-5960"


def main():
    output = ROOT / "tmp" / "integration-evidence"
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="lrste-live-check-") as folder:
        os.environ.update(DATABASE_URL="sqlite+aiosqlite:///" + (Path(folder)/"check.db").as_posix(),
            ENVIRONMENT="test", EVENT_BUS_TYPE="memory", DISABLE_AUTH="true",
            CREATE_SCHEMA_ON_STARTUP="false", VEILLE_SCHEDULER_ENABLED="false",
            MISTRAL_API_KEY="", SUPABASE_URL="", SUPABASE_PUBLISHABLE_KEY="")
        subprocess.run([sys.executable,"-m","alembic","upgrade","head"],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        import httpx
        from agents.bibliometrie.services.orcid_sync import fetch_orcid_works
        from agents.veille.services.arxiv_fetcher import fetch_arxiv
        async def fetch():
            async with httpx.AsyncClient(timeout=30) as client:
                response=await client.get(f"https://pub.orcid.org/v3.0/{ORCID}/person",headers={"Accept":"application/json"})
                response.raise_for_status()
                name=response.json()["name"]["credit-name"]["value"]
            works=await fetch_orcid_works(ORCID)
            try:
                watch=await fetch_arxiv("all:irrigation",max_results=1)
                arxiv=dict(status="success",count=len(watch))
            except Exception as error:
                arxiv=dict(status="unavailable",error=str(error))
            return name,works,arxiv
        name,works,arxiv=asyncio.run(fetch())
        (output/"live-works.json").write_text(json.dumps(works),encoding="utf-8")
        assert name == "Geoffrey Bilder", "Public identity changed; review before proceeding"
        assert works, "No works returned"
        from api.main import app
        from fastapi.testclient import TestClient
        from shared.database import engine
        evidence=dict(checked_at=datetime.now(timezone.utc).isoformat(),orcid=ORCID,name=name,
            identity_reference="https://www.crossref.org/people/geoffrey-bilder",arxiv=arxiv,
            scope="Public-source integration example; not a laboratory member or scientific validation",
            citation_metrics="Not verified: ORCID works do not supply citation counts")
        with TestClient(app) as client:
            created=client.post("/api/biblio/researchers",json=dict(name=name,email="",department="External public-source example",role="Public-source example",orcid_id=ORCID))
            created.raise_for_status()
            rid=created.json()["id"]
            # Replay the single live response for deterministic import/reimport checks.
            with patch("agents.bibliometrie.services.publication_sync.fetch_orcid_works",new=AsyncMock(return_value=works)):
                first=client.post(f"/api/biblio/researchers/{rid}/publications/sync")
                first.raise_for_status()
                second=client.post(f"/api/biblio/researchers/{rid}/publications/sync")
                second.raise_for_status()
            evidence.update(first_import=first.json(),repeat_import=second.json())
            assert second.json()["publications_created"] == 0
            assert second.json()["links_created"] == 0
            pdf=client.get(f"/api/biblio/researchers/{rid}/cv/pdf")
            pdf.raise_for_status()
            assert pdf.headers["content-type"] == "application/pdf"
            assert pdf.content.startswith(b"%PDF-")
            (output/"public-example-cv.pdf").write_bytes(pdf.content)
            evidence["pdf_bytes"]=len(pdf.content)
        asyncio.run(engine.dispose())
        (output/"evidence.json").write_text(json.dumps(evidence,indent=2),encoding="utf-8")
        print(json.dumps(evidence,indent=2))

if __name__ == "__main__": main()

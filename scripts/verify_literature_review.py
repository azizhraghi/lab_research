"""Opt-in live PubMed review check; uses only a temporary migrated database."""
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def main():
    output=ROOT/'tmp'/'integration-evidence'
    output.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='lrste-literature-') as folder:
        os.environ.update(DATABASE_URL='sqlite+aiosqlite:///'+(Path(folder)/'check.db').as_posix(),
            ENVIRONMENT='test',EVENT_BUS_TYPE='memory',DISABLE_AUTH='true',
            CREATE_SCHEMA_ON_STARTUP='false',VEILLE_SCHEDULER_ENABLED='false',
            MISTRAL_API_KEY='',SUPABASE_URL='',SUPABASE_PUBLISHABLE_KEY='')
        subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        from api.main import app
        from fastapi.testclient import TestClient
        from shared.database import engine
        with TestClient(app) as client:
            path='/api/veille/research/reviews'
            result=client.post(path,json={'topic':'water quality monitoring','max_results':3})
            result.raise_for_status()
            review=result.json()
            (output/'literature-review.json').write_text(json.dumps(review,indent=2),encoding='utf-8')
            assert review['status']=='ready',review.get('error_message')
            paper=next(item for item in review['items'] if item['abstract'])
            saved=client.patch(f"{path}/{review['id']}/items/{paper['id']}",json={
                'decision':'include','note':'Integration example only. Full text and scientific suitability have not been assessed.'})
            saved.raise_for_status()
            exported=client.get(f"{path}/{review['id']}/export")
            exported.raise_for_status()
            assert exported.json()['item_count']==1
            (output/'annotated-bibliography.txt').write_text(exported.json()['content'],encoding='utf-8')
            evidence=dict(checked_at=datetime.now(timezone.utc).isoformat(),status='success',
                query=review['topic'],records=len(review['items']),abstracts=sum(bool(i['abstract']) for i in review['items']),
                selected_title=paper['title'],selected_url=paper['url'],exported_items=1,
                scope='Live source/API integration; temporary DB; no laboratory validation or AI synthesis')
            (output/'literature-evidence.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
            print(json.dumps(evidence,indent=2))
        asyncio.run(engine.dispose())

if __name__=='__main__': main()

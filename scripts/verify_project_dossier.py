"""Offline dossier demonstration in an isolated DB, with explicitly synthetic evidence."""
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def main():
    output = ROOT/'tmp'/'integration-evidence'
    output.mkdir(parents=True, exist_ok=True)
    os.environ.update(DATABASE_URL='sqlite+aiosqlite:///'+(output/'dossier-demo.db').as_posix(),
        ENVIRONMENT='test', EVENT_BUS_TYPE='memory', DISABLE_AUTH='true',
        CREATE_SCHEMA_ON_STARTUP='false', VEILLE_SCHEDULER_ENABLED='false',
        MISTRAL_API_KEY='', SUPABASE_URL='', SUPABASE_PUBLISHABLE_KEY='')
    subprocess.run([sys.executable,'-m','alembic','upgrade','head'],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
    from api.main import app
    from fastapi.testclient import TestClient
    from shared.database import engine
    with TestClient(app) as client:
        project=client.post('/api/mis/projets/',json=dict(nom='DEMO — Water-quality research dossier',
            date_debut='2026-09-16',responsable='Demo researcher',budget_alloue=0))
        project.raise_for_status()
        pid=project.json()['id']
        path=f'/api/mis/projets/{pid}/dossier'
        result=client.put(path,json=dict(revision=0,questions='Which monitoring approach should be evaluated for the laboratory?',
            approach='Screen relevant literature, define a sampling protocol and compare measurements with a reference method.',
            findings='The workflow can connect a research question to source evidence and project deliverables. No field outcome has been measured.',
            limitations='Synthetic demonstration only. Real measurements, full-text appraisal and supervisor review remain outstanding.'))
        result.raise_for_status()
        records=[dict(title='SYNTHETIC FIXTURE — Monitoring methods example',url='https://example.invalid/synthetic-paper',
            doi=None,authors=['Demo author'],abstract='Synthetic text for software verification, not a scientific publication.',published_at=None)]
        with patch('agents.veille.research_router.fetch_pubmed',new=AsyncMock(return_value=records)):
            review=client.post('/api/veille/research/reviews',json={'topic':'DEMO water monitoring'}).json()
        item=review['items'][0]
        client.patch(f"/api/veille/research/reviews/{review['id']}/items/{item['id']}",json={'decision':'include','note':'PRIVATE demonstration annotation'}).raise_for_status()
        result=client.post(path+'/references',json=dict(revision=1,review_id=review['id'],item_id=item['id'],
            rationale='Demonstrates explicit source selection. This fixture must not support a scientific conclusion.'))
        result.raise_for_status()
        reference_id=result.json()['references'][0]['id']
        deliverable=client.post(f'/api/mis/projets/{pid}/deliverables',json=dict(title='DEMO sampling protocol',deliverable_type='protocol',notes='Synthetic handover example; field protocol needs domain review.'))
        deliverable.raise_for_status()
        did=deliverable.json()['id']
        client.patch(f'/api/mis/deliverables/{did}',json={'status':'submitted'}).raise_for_status()
        evaluation=client.post(path+'/evaluations',json=dict(revision=2,name='DEMO paired comparison',origin='synthetic',split='development',unit='mm',
            provenance='Two fabricated paired observations solely for software verification.',protocol='Model errors of +/-1 compared with baseline error of +3 on both rows.',
            rows=[dict(observed=10,predicted=11,baseline=13),dict(observed=20,predicted=19,baseline=23)]))
        evaluation.raise_for_status()
        eid=evaluation.json()['evaluations'][0]['id']
        finding=client.post(path+'/findings',json=dict(revision=3,statement='The synthetic model predictions have lower error than the synthetic baseline.',assessment='supported_with_limits',
            limitations='Only two fabricated values. This cannot establish predictive accuracy or water savings.',reference_ids=[reference_id],deliverable_ids=[did],evaluation_ids=[eid]))
        finding.raise_for_status()
        submitted=client.post(path+'/submissions',json={'revision':4})
        submitted.raise_for_status()
        from shared.security import User, get_current_user
        app.dependency_overrides[get_current_user]=lambda:User(id='demo-supervisor',role='reviewer')
        client.post(f"/api/mis/dossier-submissions/{submitted.json()['id']}/decision",json={'status':'changes_requested','feedback':'DEMO review: explicitly state which future field measurements would be needed.'}).raise_for_status()
        client.patch(f'/api/mis/deliverables/{did}',json={'status':'approved'}).raise_for_status()
        app.dependency_overrides.clear()
        current=client.get(path).json()
        narrative={key:current[key] for key in ('questions','approach','findings','limitations')}
        narrative['limitations']+=' Future evaluation needs independent soil-moisture observations with timestamps, units and a reviewed reference method.'
        client.put(path,json=dict(revision=4,**narrative)).raise_for_status()
        revised=client.post(path+'/submissions',json={'revision':5})
        revised.raise_for_status()
        app.dependency_overrides[get_current_user]=lambda:User(id='demo-supervisor',role='reviewer')
        client.post(f"/api/mis/dossier-submissions/{revised.json()['id']}/decision",json={'status':'approved','feedback':'DEMO approval of the software walkthrough only. No scientific or institutional endorsement.'}).raise_for_status()
        app.dependency_overrides.clear()
        exported=client.get(f"/api/mis/dossier-submissions/{revised.json()['id']}/export")
        exported.raise_for_status()
        assert 'PRIVATE demonstration' not in exported.json()['content']
        (output/'project-dossier.html').write_text(exported.json()['content'],encoding='utf-8')
        (output/'dossier-demo.json').write_text(json.dumps(dict(project_id=pid,submission_id=revised.json()['id'],dossier=client.get(path).json()),indent=2),encoding='utf-8')
        print('Verified dossier API workflow and wrote isolated demo/export: '+pid)
    asyncio.run(engine.dispose())

if __name__=='__main__': main()

"""Isolated submission audit. Uses audit-2026-09-07.db, never the lab database."""
import os
import sys
import json
import time
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.update(DATABASE_URL='sqlite+aiosqlite:///./audit-2026-09-07.db',
                  EVENT_BUS_TYPE='memory', VEILLE_SCHEDULER_ENABLED='false',
                  ENVIRONMENT='test', DISABLE_AUTH='true', CREATE_SCHEMA_ON_STARTUP='false')
from fastapi.testclient import TestClient
from api.main import app
from shared.security import get_current_user, User

results = []
def record(name, value):
    results.append({'check': name, 'result': value})
    print(name, json.dumps(value, default=str), flush=True)

with TestClient(app, raise_server_exceptions=False) as client:
    def req(method, path, body=None):
        r = client.request(method, path, json=body) if body is not None else client.request(method, path)
        try: data = r.json()
        except ValueError: data = r.text[:250]
        return r.status_code, data
    record('ready', req('GET', '/ready'))
    schema = client.get('/openapi.json').json()
    record('api_operation_count', sum(m in {'get','post','put','patch','delete'} for p in schema['paths'].values() for m in p))
    list_results = {}
    for path in schema['paths']:
        if '{' not in path and 'get' in schema['paths'][path]:
            status, data = req('GET', path)
            list_results[path] = {'status':status, 'count':len(data) if isinstance(data,list) else None}
    record('unparameterized_gets', list_results)
    status, project = req('POST','/api/mis/projets/', {'nom':'AUDIT synthetic project','date_debut':'2026-09-07','responsable':'Audit','budget_alloue':1000})
    record('create_project', status)
    record('update_project_date', req('PUT', '/api/mis/projets/'+project['id'], {'date_fin_prevue':'2026-12-01'}))
    parcel_body={'name':'AUDIT synthetic parcel','code':'AUDIT-'+str(time.time_ns()), 'area_ha':1,'latitude':36.8,'longitude':10.1,'project_id':project['id']}
    status, parcel = req('POST','/api/twin/parcels',parcel_body)
    record('create_parcel', status)
    pid=parcel['id']
    status, reading=req('POST',f'/api/twin/parcels/{pid}/readings',{'recorded_at':'2026-09-07T08:00:00','soil_moisture_mm':60,'rainfall_mm':0,'evapotranspiration_mm':4,'data_origin':'test'})
    record('create_reading', status)
    recs=[]
    for _ in range(40):
        time.sleep(.2)
        recs=client.get('/api/twin/recommendations').json()
        recs=[r for r in recs if r['parcel_id']==pid]
        if recs: break
    record('automatic_recommendation',recs)
    if recs:
        rid=recs[0]['id']
        application={'recommendation_id':rid,'occurred_at':'2026-09-07T09:00:00','amount_mm':20,'method':'manual','recorded_by':'AUDIT'}
        record('application_before_approval',req('POST',f'/api/twin/parcels/{pid}/irrigation-events',application))
        async def researcher(): return User(id='audit-researcher',role='researcher')
        app.dependency_overrides[get_current_user]=researcher
        record('researcher_cannot_approve',req('PATCH',f'/api/twin/recommendations/{rid}/approve')[0])
        app.dependency_overrides.clear()
        record('admin_approval',req('PATCH',f'/api/twin/recommendations/{rid}/approve')[0])
        record('application_after_approval',req('POST',f'/api/twin/parcels/{pid}/irrigation-events',application))
    status,bad=req('POST',f'/api/twin/parcels/{pid}/readings',{'recorded_at':'2026-09-07T10:00:00','soil_moisture_mm':999,'data_origin':'test'})
    time.sleep(2)
    _, rows=req('GET',f'/api/twin/parcels/{pid}/readings')
    record('suspect_reading_quality',[(r['id'],r['quality_flag'],r['review_status']) for r in rows if r['id']==bad['id']])
    record('manual_recommend_from_suspect',req('POST',f'/api/twin/parcels/{pid}/recommend'))
    record('public_excludes_internal_project',req('GET','/api/public/projects'))
    record('invalid_parcel_parameters',req('POST','/api/twin/parcels',{**parcel_body,'code':'INVALID-'+str(time.time_ns()),'area_ha':-1,'latitude':999,'field_capacity_mm':-10,'wilting_point_mm':45})[0])
    record('final_ready',req('GET','/ready'))
    from shared.config import settings
    settings.DISABLE_AUTH = False
    settings.SUPABASE_URL = 'https://audit.example.invalid'
    settings.SUPABASE_PUBLISHABLE_KEY = 'audit-placeholder'
    record('anonymous_public_get', req('GET','/api/public/projects')[0])
    record('anonymous_private_get', req('GET','/api/mis/projets/')[0])
    record('anonymous_public_admin_get', req('GET','/api/public/admin/projects')[0])
    settings.DISABLE_AUTH = True

import asyncio
from unittest.mock import patch, AsyncMock
from agents.veille.agent import veille_agent
from agents.veille.models import Source
from shared.database import AsyncSessionLocal
async def watch_failure_probe():
    async with AsyncSessionLocal() as db:
        db.add(Source(name='AUDIT unavailable RSS',url='https://audit.example.invalid/feed',type='rss',active=True))
        await db.commit()
        with patch('agents.veille.services.scraper.httpx.AsyncClient.get',new=AsyncMock(side_effect=RuntimeError('AUDIT simulated fetch failure'))):
            run=await veille_agent.run_collection(db)
        record('rss_failure_collection_outcome', {'status':run.status,'error_message':run.error_message,'articles_collected':run.articles_collected})
asyncio.run(watch_failure_probe())

for name in ['multiagent.db','lrste-demo.db']:
    connection=sqlite3.connect(f'file:{ROOT / name}?mode=ro',uri=True)
    tables=[r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    counts={t:connection.execute('SELECT count(*) FROM "'+t+'"').fetchone()[0] for t in tables}
    record(name+'_counts',counts)
    if 'twin_sensor_readings' in tables:
        record(name+'_reading_origins',connection.execute('SELECT data_origin,count(*) FROM twin_sensor_readings GROUP BY data_origin').fetchall())
    connection.close()
Path('docs/audit-2026-09-07-evidence.json').write_text(json.dumps(results,indent=2,default=str),encoding='utf-8')

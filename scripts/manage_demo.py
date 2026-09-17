"""Operations checks for the isolated, localhost-only compose.demo.yml package."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import shutil
import time
import urllib.request
from uuid import uuid4, UUID

ROOT=Path(__file__).resolve().parents[1]
COMPOSE=['docker','compose','-f',str(ROOT/'compose.demo.yml')]

def docker(*args,input=None):
    return subprocess.run([*COMPOSE,*args],cwd=ROOT,input=input,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=True,timeout=180).stdout


def preflight():
    """Read-only environment checks; never install software or start containers."""
    checks=[]
    for name in ('compose.demo.yml','deploy/Dockerfile.api','deploy/Dockerfile.web','deploy/nginx.conf','requirements/locked.txt'):
        checks.append(dict(check=name,status='passed' if (ROOT/name).is_file() else 'failed'))
    if not shutil.which('docker'):
        checks.append(dict(check='Docker runtime',status='blocked',detail='Docker executable is not available on PATH.'))
    else:
        for name,args in [('Compose configuration',('config','--quiet')),('Container runtime',('ps',))]:
            try:
                docker(*args)
                checks.append(dict(check=name,status='passed'))
            except (subprocess.SubprocessError,OSError):
                checks.append(dict(check=name,status='blocked',detail='Command failed. Check Docker Desktop and Compose configuration locally.'))
    return dict(ready=all(c['status']=='passed' for c in checks),checks=checks,
        scope='Local demonstration readiness only. No deployment, restore or broker recovery has been executed by preflight.')

def request(path,body=None):
    data=None if body is None else json.dumps(body).encode()
    req=urllib.request.Request('http://127.0.0.1:8080'+path,data=data,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=10) as response: return json.load(response)

def wait_ready():
    for _ in range(60):
        try:
            if request('/ready')['status']=='ready': return
        except Exception: pass
        time.sleep(2)
    raise RuntimeError('Demo did not become ready within 120 seconds')

def backup(destination):
    destination=Path(destination)
    if destination.exists(): raise ValueError('Choose a new backup path; existing files are never overwritten.')
    destination.parent.mkdir(parents=True,exist_ok=True)
    payload=docker('exec','-T','db','pg_dump','-U','lab','-d','laboratory','-Fc')
    if not payload.startswith(b'PGDMP'): raise RuntimeError('Unexpected dump format')
    with destination.open('xb') as stream: stream.write(payload)
    return dict(bytes=len(payload),path=str(destination))

def restore_check(source):
    # Never restore over the application database. Keep the new DB for inspection.
    target='restore_check_'+uuid4().hex[:12]
    docker('exec','-T','db','createdb','-U','lab',target)
    docker('exec','-T','db','pg_restore','-U','lab','--exit-on-error','--no-owner','-d',target,input=Path(source).read_bytes())
    revision=docker('exec','-T','db','psql','-U','lab','-d',target,'-Atc','SELECT version_num FROM alembic_version').decode().strip()
    count=docker('exec','-T','db','psql','-U','lab','-d',target,'-Atc','SELECT count(*) FROM projets').decode().strip()
    if not revision: raise RuntimeError('Restored database has no migration revision')
    return dict(restored_database=target,migration=revision,projects=int(count))

def fault_check():
    wait_ready()
    project=None
    docker('stop','redis')
    try:
        project=request('/api/mis/projets/',dict(nom='RECOVERY TEST '+uuid4().hex[:8],date_debut='2026-01-01',responsable='Synthetic recovery check',budget_alloue=0))
        time.sleep(3)
    finally:
        docker('start','redis')
    wait_ready()
    # Verify this project's event reached the outbox's delivered state, not only readiness.
    project_id=str(UUID(project['id']))
    for _ in range(30):
        query="SELECT count(*) FROM system_outbox o JOIN system_event_receipts r ON r.event_id=o.id WHERE o.status='delivered' AND o.event->>'type'='projet.created' AND o.event->'payload'->>'id'='"+project_id+"' AND r.agent_name='orchestrateur' AND r.status='processed'"
        count=docker('exec','-T','db','psql','-U','lab','-d','laboratory','-Atc',query).decode().strip()
        if int(count)>0: return dict(project_id=project['id'],delivery_recovered=True,orchestrator_processed=True)
        time.sleep(2)
    raise RuntimeError('Project event was not delivered and processed by the orchestrator after Redis restart')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['preflight','check','backup','restore-check','fault-check'])
    parser.add_argument('--file')
    parser.add_argument('--report',help='Write results to a new JSON file; existing files are never overwritten')
    args=parser.parse_args()
    if args.report and Path(args.report).exists(): parser.error('Report already exists; choose a new path.')
    if args.action=='preflight': result=preflight()
    elif args.action=='check':
        wait_ready(); result=dict(health=request('/health'),readiness=request('/ready'))
    elif args.action in ('backup','restore-check'):
        if not args.file: parser.error('--file is required')
        result=backup(args.file) if args.action=='backup' else restore_check(args.file)
    else: result=fault_check()
    record=json.dumps(dict(checked_at=datetime.now(timezone.utc).isoformat(),action=args.action,result=result),indent=2)
    if args.report:
        destination=Path(args.report)
        destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('x',encoding='utf-8') as stream: stream.write(record+'\n')
    print(record)
    if args.action=='preflight' and not result['ready']: raise SystemExit(2)

if __name__=='__main__':main()

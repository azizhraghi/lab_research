"""Offline regression suite. All writes use a migrated temporary SQLite DB."""
import asyncio
from datetime import datetime, timedelta
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
TEST_DIR = tempfile.TemporaryDirectory(prefix="lrste-regression-")
os.environ.update(
    DATABASE_URL="sqlite+aiosqlite:///" + (Path(TEST_DIR.name) / "test.db").as_posix(),
    EVENT_BUS_TYPE="memory", ENVIRONMENT="test", DISABLE_AUTH="true",
    CREATE_SCHEMA_ON_STARTUP="false", VEILLE_SCHEDULER_ENABLED="false",
    MISTRAL_API_KEY="", SUPABASE_URL="", SUPABASE_PUBLISHABLE_KEY="",
)
subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=ROOT, check=True,
               stdout=subprocess.DEVNULL)

from fastapi.testclient import TestClient
from sqlalchemy import select, update
from api.main import app
from shared.database import AsyncSessionLocal, engine
from shared.security import User, get_current_user
from agents.digitaltwin.models import SensorReading, WeatherForecast
from agents.veille.models import Source
from agents.veille.agent import veille_agent


class WorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)
        asyncio.run(engine.dispose())
        TEST_DIR.cleanup()

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_guided_staff_assignment_preserves_existing_assignments(self):
        def project():
            return self.client.post('/api/mis/projets/',json=dict(nom='Setup fixture',date_debut='2026-01-01',responsable='Fixture')).json()['id']
        first,second=project(),project()
        staff=self.client.post('/api/mis/personnels/',json=dict(nom='Fixture',prenom='Setup',email=str(uuid4())+'@example.test',role='chercheur')).json()
        path=f'/api/mis/projets/{first}/assign-staff'
        self.assertEqual(self.client.post(path,json={'personnel_id':staff['id']}).status_code,200)
        self.assertEqual(self.client.get(f"/api/mis/personnels/{staff['id']}").json()['projet_actuel_id'],first)
        self.assertEqual(self.client.post(f'/api/mis/projets/{second}/assign-staff',json={'personnel_id':staff['id']}).status_code,409)
        self.assertEqual(self.client.get(f"/api/mis/personnels/{staff['id']}").json()['projet_actuel_id'],first)
        self.assertEqual(self.client.post('/api/mis/projets/missing/assign-staff',json={'personnel_id':staff['id']}).status_code,404)
        app.dependency_overrides[get_current_user]=lambda:User(id='viewer',role='viewer')
        self.assertEqual(self.client.post(path,json={'personnel_id':staff['id']}).status_code,403)

    def test_parcel_evidence_trail_preserves_demo_gate_and_isolation(self):
        pid=self.parcel(); other=self.parcel()
        path=f'/api/twin/parcels/{pid}/evidence-trail'
        self.assertFalse(self.client.get(path).json()['eligibility']['eligible'])
        reading=self.reading(pid,origin='demo')
        self.reading(other,origin='demo')
        result=self.client.get(path)
        self.assertEqual(result.status_code,200,result.text)
        self.assertFalse(result.json()['eligibility']['eligible'])
        self.assertEqual([r['id'] for r in result.json()['readings']],[reading['id']])
        self.assertEqual(result.json()['readings'][0]['origin'],'demo')
        self.assertEqual(self.client.get('/api/twin/parcels/999999/evidence-trail').status_code,404)

    def test_publication_audit_reports_gaps_without_claiming_verification(self):
        from agents.bibliometrie.models import Publication,ResearcherPublication
        researcher=self.client.post('/api/biblio/researchers',json=dict(name='Audit fixture',email=str(uuid4())+'@example.test',department='Demo',role='Researcher')).json()
        async def seed():
            async with AsyncSessionLocal() as db:
                for title in ['Water quality study','WATER quality study!']:
                    row=Publication(title=title,source='manual')
                    db.add(row);await db.flush()
                    db.add(ResearcherPublication(researcher_id=researcher['id'],publication_id=row.id))
                await db.commit()
        asyncio.run(seed())
        result=self.client.get(f"/api/biblio/researchers/{researcher['id']}/publication-audit")
        self.assertEqual(result.status_code,200,result.text)
        self.assertEqual(result.json()['needs_attention'],2)
        self.assertTrue(all(any('Repeated title' in issue for issue in r['issues']) for r in result.json()['publications']))
        self.assertIn('not independently verified',result.json()['validation'])

    def test_literature_screening_export_and_ownership(self):
        path='/api/veille/research/reviews'
        record=dict(title='Water monitoring study',url='https://pubmed.ncbi.nlm.nih.gov/1/',
                    doi='10.1234/example',authors=['Example Author'],abstract='Methods: Water was sampled.',published_at=None)
        records=[record,{**record,'doi':'https://doi.org/10.1234/EXAMPLE'},
                 {**record,'title':'Metadata only paper','doi':None,'url':'https://pubmed.ncbi.nlm.nih.gov/2/','abstract':None}]
        with patch('agents.veille.research_router.fetch_pubmed',new=AsyncMock(return_value=records)):
            result=self.client.post(path,json={'topic':'water monitoring'})
        self.assertEqual(result.status_code,200,result.text)
        review=result.json()
        self.assertEqual(review['status'],'ready')
        self.assertEqual(len(review['items']),2)
        self.assertIsNone(review['items'][1]['evidence_excerpt'])
        export=f"{path}/{review['id']}/export"
        item=f"{path}/{review['id']}/items/{review['items'][0]['id']}"
        self.assertEqual(self.client.get(export).status_code,409)
        self.assertEqual(self.client.patch(item,json={'decision':'include','note':'Check sampling limitations.'}).status_code,200)
        exported=self.client.get(export).json()
        self.assertEqual(exported['item_count'],1)
        self.assertIn('Check sampling limitations.',exported['content'])
        self.assertNotIn('Metadata only paper',exported['content'])
        stored=next(r for r in self.client.get(path).json() if r['id']==review['id'])
        self.assertEqual(stored['items'][0]['decision'],'include')
        app.dependency_overrides[get_current_user]=lambda:User(id='other-reviewer',role='researcher')
        self.assertEqual(self.client.get(path).json(),[])
        self.assertEqual(self.client.get(export).status_code,404)
        self.assertEqual(self.client.patch(item,json={'decision':'exclude'}).status_code,404)
        app.dependency_overrides[get_current_user]=lambda:User(id='dev',role='viewer')
        self.assertEqual(self.client.post(path,json={'topic':'water'}).status_code,403)
        self.assertEqual(self.client.patch(item,json={'decision':'exclude'}).status_code,403)

    def test_literature_source_failure_is_persisted(self):
        with patch('agents.veille.research_router.fetch_pubmed',new=AsyncMock(side_effect=RuntimeError('Source unavailable'))):
            result=self.client.post('/api/veille/research/reviews',json={'topic':'water monitoring'})
        self.assertEqual(result.status_code,200,result.text)
        self.assertEqual(result.json()['status'],'failed')
        self.assertIn('Source unavailable',result.json()['error_message'])
        self.assertEqual(result.json()['items'],[])

    def test_pubmed_abstract_parser_preserves_source_sections(self):
        from agents.veille.services.pubmed_fetcher import parse_pubmed_records
        xml='''<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>123</PMID><Article>
        <ArticleTitle>Water <i>quality</i> study</ArticleTitle><Abstract>
        <AbstractText Label="METHODS">Collected <b>samples</b>.</AbstractText>
        <AbstractText Label="RESULTS">Measured quality.</AbstractText></Abstract>
        <AuthorList><Author><ForeName>Ada</ForeName><LastName>Example</LastName></Author></AuthorList>
        <Journal><JournalIssue><PubDate><Year>2026</Year><Month>09</Month><Day>11</Day></PubDate></JournalIssue></Journal>
        </Article></MedlineCitation><PubmedData><ArticleIdList><ArticleId IdType="doi">10.1234/test</ArticleId></ArticleIdList></PubmedData>
        </PubmedArticle></PubmedArticleSet>'''
        paper=parse_pubmed_records(xml)[0]
        self.assertEqual(paper['title'],'Water quality study')
        self.assertEqual(paper['abstract'],'METHODS: Collected samples.\nRESULTS: Measured quality.')
        self.assertEqual(paper['published_at'].month,9)
        self.assertEqual(paper['authors'],['Ada Example'])
        with self.assertRaises(RuntimeError):
            parse_pubmed_records('<eFetchResult><ERROR>Invalid request</ERROR></eFetchResult>')

    def test_project_dossier_evidence_export_and_conflicts(self):
        project=self.client.post('/api/mis/projets/',json=dict(nom='Dossier <script>alert(1)</script>',
            date_debut='2026-01-01',responsable='Test lead',budget_alloue=0)).json()
        path=f"/api/mis/projets/{project['id']}/dossier"
        self.assertEqual(self.client.get(path).json()['revision'],0)
        narrative=dict(revision=0,questions='Can the approach help?',approach='Compare sources.',
                       findings='<img src=x onerror=alert(1)>',limitations='No independent field validation.')
        saved=self.client.put(path,json=narrative)
        self.assertEqual(saved.status_code,200,saved.text)
        self.assertEqual(saved.json()['revision'],1)
        self.assertEqual(self.client.put(path,json=narrative).status_code,409)
        records=[dict(title='Water evidence',url='https://pubmed.ncbi.nlm.nih.gov/123/',doi='10.1234/dossier',
            authors=['Example Author'],abstract='Source abstract evidence.',published_at=None)]
        with patch('agents.veille.research_router.fetch_pubmed',new=AsyncMock(return_value=records)):
            review=self.client.post('/api/veille/research/reviews',json={'topic':'water evidence'}).json()
        item=review['items'][0]
        body=dict(revision=1,review_id=review['id'],item_id=item['id'],rationale='Supports the planned method.')
        self.assertEqual(self.client.post(path+'/references',json=body).status_code,409)
        self.client.patch(f"/api/veille/research/reviews/{review['id']}/items/{item['id']}",
            json={'decision':'include','note':'PRIVATE-NOTE-MUST-STAY-PRIVATE'})
        app.dependency_overrides[get_current_user]=lambda:User(id='other-researcher',role='researcher')
        self.assertEqual(self.client.post(path+'/references',json=body).status_code,404)
        app.dependency_overrides.clear()
        attached=self.client.post(path+'/references',json=body)
        self.assertEqual(attached.status_code,200,attached.text)
        self.assertEqual(attached.json()['revision'],2)
        self.assertNotIn('PRIVATE-NOTE',attached.text)
        self.assertEqual(self.client.post(path+'/references',json={**body,'revision':2}).status_code,409)
        ref=attached.json()['references'][0]
        self.client.patch(f"/api/veille/research/reviews/{review['id']}/items/{item['id']}",json={'decision':'exclude','note':'Later changed'})
        current=self.client.get(path).json()
        self.assertEqual(current['references'][0]['title'],'Water evidence')
        exported=self.client.get(path+'/export')
        self.assertEqual(exported.status_code,200,exported.text)
        html=exported.json()['content']
        self.assertIn('Supports the planned method.',html)
        self.assertIn('No deliverables recorded.',html)
        self.assertIn('&lt;script&gt;',html)
        self.assertNotIn('<script>',html)
        self.assertNotIn('<img src',html)
        self.assertNotIn('PRIVATE-NOTE',html)
        self.assertEqual(self.client.delete(path+f"/references/{ref['id']}?revision=1").status_code,409)
        removed=self.client.delete(path+f"/references/{ref['id']}?revision=2")
        self.assertEqual(removed.status_code,200,removed.text)
        self.assertEqual(removed.json()['references'],[])
        self.assertEqual(removed.json()['questions'],narrative['questions'])
        app.dependency_overrides[get_current_user]=lambda:User(id='viewer',role='viewer')
        self.assertEqual(self.client.get(path).status_code,200)
        self.assertEqual(self.client.put(path,json={**narrative,'revision':3}).status_code,403)
        self.assertEqual(self.client.post(path+'/references',json=body).status_code,403)
        self.assertEqual(self.client.delete(path+f"/references/{ref['id']}?revision=3").status_code,403)

    def test_project_dossier_rejects_missing_projects_and_invalid_payloads(self):
        path='/api/mis/projets/missing-project/dossier'
        self.assertEqual(self.client.get(path).status_code,404)
        self.assertEqual(self.client.get(path+'/export').status_code,404)
        self.assertEqual(self.client.put(path,json=dict(revision=0,questions='',approach='',findings='',limitations='')).status_code,404)
        self.assertEqual(self.client.put(path,json={'revision':0,'questions':None}).status_code,422)

    def test_evidence_evaluation_submission_and_independent_review(self):
        project=self.client.post('/api/mis/projets/',json=dict(nom='Review workflow fixture',date_debut='2026-01-01',responsable='Fixture lead',budget_alloue=0)).json()
        path=f"/api/mis/projets/{project['id']}/dossier"
        narrative=dict(revision=0,questions='Which approach should we evaluate?',approach='Paired baseline comparison',findings='',limitations='Synthetic values only; field validation pending.')
        self.assertEqual(self.client.put(path,json=narrative).status_code,200)
        self.assertEqual(self.client.post(path+'/submissions',json={'revision':1}).status_code,422)
        evaluation=dict(revision=1,name='Synthetic paired comparison',origin='synthetic',split='development',unit='mm',
            provenance='Generated fixture values, no field data.',protocol='Compare model and constant-error baseline on identical pairs.',
            rows=[dict(observed=10,predicted=11,baseline=13),dict(observed=20,predicted=19,baseline=23)])
        result=self.client.post(path+'/evaluations',json=evaluation)
        self.assertEqual(result.status_code,200,result.text)
        run=result.json()['evaluations'][0]
        self.assertEqual(run['model_metrics'],dict(mae=1,rmse=1,bias=0))
        self.assertEqual(run['baseline_metrics'],dict(mae=3,rmse=3,bias=3))
        finding=dict(revision=2,statement='Fixture predictions have lower paired error.',assessment='supported_with_limits',
            limitations='Synthetic demonstration; no claim about field accuracy.',reference_ids=[],deliverable_ids=[],evaluation_ids=['wrong-project-evidence'])
        self.assertEqual(self.client.post(path+'/findings',json=finding).status_code,422)
        finding['evaluation_ids']=[run['id']]
        result=self.client.post(path+'/findings',json=finding)
        self.assertEqual(result.status_code,200,result.text)
        created=self.client.post(path+'/submissions',json={'revision':3})
        self.assertEqual(created.status_code,200,created.text)
        submission=created.json(); sid=submission['id']
        self.assertEqual(self.client.post(path+'/submissions',json={'revision':3}).status_code,409)
        decision_path=f'/api/mis/dossier-submissions/{sid}/decision'
        self.assertEqual(self.client.post(decision_path,json={'status':'approved','feedback':'I reviewed this demonstration.'}).status_code,403)
        before=self.client.get(f'/api/mis/dossier-submissions/{sid}').json()['snapshot']
        self.assertEqual(self.client.put(path,json={**narrative,'revision':3,'questions':'A changed working research question'}).status_code,200)
        app.dependency_overrides[get_current_user]=lambda:User(id='independent-reviewer',role='reviewer')
        decided=self.client.post(decision_path,json={'status':'changes_requested','feedback':'Please add an explicit measurement protocol.'})
        self.assertEqual(decided.status_code,200,decided.text)
        self.assertEqual(self.client.post(decision_path,json={'status':'approved','feedback':'Second decision should be rejected.'}).status_code,409)
        app.dependency_overrides.clear()
        after=self.client.get(f'/api/mis/dossier-submissions/{sid}').json()['snapshot']
        self.assertEqual(before,after)
        revised=self.client.post(path+'/submissions',json={'revision':4}).json()
        comparison=self.client.get(f"/api/mis/dossier-submissions/{revised['id']}/comparison?against={sid}")
        self.assertEqual(comparison.status_code,200,comparison.text)
        self.assertEqual([c['field'] for c in comparison.json()['changes']],['questions'])
        self.assertEqual(comparison.json()['changes'][0]['before'],narrative['questions'])
        self.assertEqual(comparison.json()['changes'][0]['after'],'A changed working research question')
        app.dependency_overrides[get_current_user]=lambda:User(id='independent-reviewer',role='reviewer')
        approved=self.client.post(f"/api/mis/dossier-submissions/{revised['id']}/decision",json={'status':'approved','feedback':'Reviewed revised synthetic demonstration; field evidence is still required.'})
        self.assertEqual(approved.status_code,200,approved.text)
        export=self.client.get(f"/api/mis/dossier-submissions/{revised['id']}/export").json()['content']
        self.assertIn('Status: approved',export)
        self.assertNotIn('this export is not supervisor approval',export)
        self.assertIn('Synthetic paired comparison',export)
        self.assertIn('independent-reviewer',export)
        self.assertEqual(len(self.client.get(path+'/submissions').json()),2)
        app.dependency_overrides[get_current_user]=lambda:User(id='read-only',role='viewer')
        self.assertEqual(self.client.post(path+'/evaluations',json={**evaluation,'revision':4}).status_code,403)
        self.assertEqual(self.client.post(path+'/submissions',json={'revision':4}).status_code,403)

    def test_bibliographic_identity_review_invalidates_after_identifier_change(self):
        researcher=self.client.post('/api/biblio/researchers',json=dict(name='Identity fixture',email=str(uuid4())+'@example.test',department='Demo',role='Researcher',orcid_id='0000-0002-1825-0097')).json()
        path=f"/api/biblio/researchers/{researcher['id']}/trust"
        trust=self.client.get(path).json()
        self.assertEqual(trust['identity_status'],'needs_review')
        body=dict(identifiers=trust['identifiers'],rationale='Synthetic identity check for workflow tests, not a real identity assertion.')
        confirmed=self.client.post(path,json=body)
        self.assertEqual(confirmed.status_code,200,confirmed.text)
        self.assertEqual(confirmed.json()['identity_status'],'manually_confirmed')
        self.client.put(f"/api/biblio/researchers/{researcher['id']}",json={'name':'Changed identity fixture'})
        self.assertEqual(self.client.get(path).json()['identity_status'],'needs_review')
        self.assertEqual(self.client.post(path,json=body).status_code,409)
        app.dependency_overrides[get_current_user]=lambda:User(id='ordinary-researcher',role='researcher')
        self.assertEqual(self.client.post(path,json=body).status_code,403)

    def test_metric_source_is_explicit_not_inferred_from_identifiers(self):
        from agents.bibliometrie.agent import bibliometrie_agent
        researcher=self.client.post('/api/biblio/researchers',json=dict(name='Metric fixture',email=str(uuid4())+'@example.test',department='Demo',role='Researcher',scholar_id='fixture-id')).json()
        def fallback(profile):
            profile.h_index=2
            profile.citation_count=7
            profile.metrics_source='openalex'
            return profile
        with patch.object(bibliometrie_agent,'fetch_scholar_metrics',side_effect=fallback):
            result=self.client.post(f"/api/biblio/researchers/{researcher['id']}/sync")
        self.assertEqual(result.status_code,200,result.text)
        metrics=self.client.get(f"/api/biblio/researchers/{researcher['id']}/trust").json()['metrics']
        self.assertEqual(len(metrics),2)
        self.assertTrue(all(m['source']=='openalex' for m in metrics))

    def parcel(self):
        r = self.client.post('/api/twin/parcels', json=dict(
            name='Regression fixture', code=str(uuid4()), area_ha=1, latitude=36.8, longitude=10.1))
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()['id']

    def reading(self, pid, moisture=60, origin='field', when=None):
        # "field" is an explicitly synthetic input fixture in the temporary DB.
        r = self.client.post(f'/api/twin/parcels/{pid}/readings', json=dict(
            recorded_at=(when or datetime.utcnow()).isoformat(), soil_moisture_mm=moisture,
            rainfall_mm=0, evapotranspiration_mm=4, data_origin=origin))
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def until(self, check):
        deadline = time.monotonic() + 12
        while time.monotonic() < deadline:
            result = check()
            if result:
                return result
            time.sleep(.1)
        self.fail('Background workflow did not reach expected state within 12 seconds')

    def recommendations(self, pid):
        return [r for r in self.client.get('/api/twin/recommendations?limit=100').json() if r['parcel_id'] == pid]

    def reviewed(self, pid, rid):
        return self.until(lambda: next((r for r in self.client.get(f'/api/twin/parcels/{pid}/readings').json()
                                       if r['id']==rid and r['review_status']!='pending_validation'), None))

    def test_institutional_publishing_lifecycle_and_permissions(self):
        for kind, fields in [("news", {}), ("events", {"event_date": "2026-10-01", "location": "Lab"}),
                             ("theses", {"author": "Synthetic author", "supervisor": "Synthetic supervisor", "degree": "Masters"})]:
            with self.subTest(kind=kind):
                body = dict(kind=kind, title="Synthetic test record", body="Synthetic content for isolated workflow verification.", **fields)
                created = self.client.post('/api/public/admin/content', json=body)
                self.assertEqual(created.status_code, 200, created.text)
                item = created.json()
                path = f"/api/public/admin/content/{item['id']}"
                public = f'/api/public/content?kind={kind}'
                def visible():
                    return any(r['id'] == item['id'] for r in self.client.get(public).json())
                self.assertFalse(visible())
                self.assertEqual(self.client.patch(path+'/status', json={'status':'published'}).status_code, 200)
                self.assertTrue(visible())
                self.assertNotIn('approved_by', self.client.get(public).json()[0])
                body['title'] = 'Revised synthetic record'
                self.assertEqual(self.client.put(path, json=body).json()['status'], 'draft')
                self.assertFalse(visible())
                self.client.patch(path+'/status', json={'status':'published'})
                self.assertEqual(self.client.patch(path+'/status', json={'status':'withdrawn'}).status_code, 200)
                self.assertFalse(visible())
                for role in ['viewer', 'researcher', 'reviewer']:
                    async def identity(role=role): return User(id='role-fixture', role=role)
                    app.dependency_overrides[get_current_user] = identity
                    self.assertEqual(self.client.post('/api/public/admin/content', json=body).status_code, 403)
                    self.assertEqual(self.client.put(path, json=body).status_code, 403)
                    self.assertEqual(self.client.patch(path+'/status', json={'status':'published'}).status_code, 403)
                app.dependency_overrides.clear()
        from shared.config import settings
        with patch.object(settings, 'DISABLE_AUTH', False):
            self.assertEqual(self.client.get('/api/public/content?kind=news').status_code, 200)
            self.assertEqual(self.client.get('/api/public/admin/content?kind=news').status_code, 503)
            with patch.object(settings, 'SUPABASE_URL', 'https://auth.example.invalid'), patch.object(settings, 'SUPABASE_PUBLISHABLE_KEY', 'test-public-key'):
                self.assertEqual(self.client.get('/api/public/admin/content?kind=news').status_code, 401)

    def test_institutional_content_rejects_invalid_fields(self):
        base = dict(kind='news', title='Test record', body='Synthetic content with enough length.')
        for overrides in [dict(title='   '), dict(kind='events'), dict(kind='theses'),
                          dict(link='javascript:alert(1)'), dict(status='published'),
                          dict(kind='events', event_date='2026-10-02', end_date='2026-10-01', location='Lab')]:
            response = self.client.post('/api/public/admin/content', json={**base, **overrides})
            self.assertEqual(response.status_code, 422, response.text)

    def test_project_lifecycle_and_project_wide_report(self):
        project = self.client.post('/api/mis/projets/', json=dict(nom='Synthetic lifecycle', responsable='Test lead', date_debut='2026-01-01', statut='planifie')).json()
        pid = project['id']
        base = f'/api/mis/projets/{pid}'
        self.assertEqual(self.client.put(base, json={'statut':'en_cours'}).status_code, 200)
        staff = self.client.post('/api/mis/personnels/', json=dict(nom='Fixture', prenom='Synthetic', email='fixture@example.invalid', role='chercheur', projet_actuel_id=pid))
        self.assertEqual(staff.status_code, 200, staff.text)
        milestone = self.client.post(base+'/milestones', json=dict(title='First milestone', due_date='2026-01-15')).json()
        deliverable = self.client.post(base+'/deliverables', json=dict(title='Final report')).json()
        risk = self.client.post(base+'/risks', json=dict(title='Test risk')).json()
        report = self.client.get(base+'/completion-report')
        self.assertEqual(report.status_code, 200, report.text)
        self.assertEqual(len(report.json()['outstanding']), 3)
        budget = self.client.post('/api/mis/budgets/', json=dict(projet_id=pid, montant_alloue=1000, devise='EUR', date_debut='2026-01-01')).json()
        entry = self.client.post('/api/mis/budgets/entries', json=dict(budget_id=budget['id'], entry_type='expense', description='Synthetic supplies', amount=125, occurred_at='2026-01-12'))
        self.assertEqual(entry.status_code, 200, entry.text)
        self.assertEqual(self.client.patch(f"/api/mis/milestones/{milestone['id']}",json={'status':None}).status_code,422)
        self.client.patch(f"/api/mis/milestones/{milestone['id']}",json={'status':'completed'})
        path = f"/api/mis/deliverables/{deliverable['id']}"
        self.assertEqual(self.client.patch(path,json={'status':'approved'}).status_code,409)
        self.assertEqual(self.client.patch(path,json={'status':'submitted'}).status_code,200)
        async def researcher(): return User(id='researcher-fixture',role='researcher')
        app.dependency_overrides[get_current_user]=researcher
        self.assertEqual(self.client.patch(path,json={'status':'approved'}).status_code,403)
        app.dependency_overrides.clear()
        self.assertEqual(self.client.patch(path,json={'status':'approved'}).status_code,200)
        self.client.patch(f"/api/mis/risks/{risk['id']}",json={'status':'mitigated'})
        self.assertEqual(self.client.put(base,json={'statut':'termine'}).status_code,200)
        report=self.client.get(base+'/completion-report').json()
        self.assertEqual(report['outstanding'],[])
        self.assertEqual(report['project']['statut'],'termine')
        self.assertEqual(len(report['staff']),1)
        self.assertEqual(report['budgets'][0]['spent'],125)
        self.assertEqual(report['budgets'][0]['available'],875)
        self.assertEqual(len(report['entries']),1)
        edited=self.client.patch(path,json={'title':'Revised final report'})
        self.assertEqual(edited.json()['status'],'draft')
        self.assertIsNone(edited.json()['submitted_at'])
        self.assertTrue(self.client.get(base+'/completion-report').json()['outstanding'])

    def test_bibliography_normalization_reimport_and_cv_delivery(self):
        from agents.bibliometrie.services.orcid_sync import normalise_doi
        self.assertEqual(normalise_doi('  HTTPS://doi.org/10.1234/ABC  '),'10.1234/abc')
        researcher=self.client.post('/api/biblio/researchers',json=dict(name='Synthetic <b>literal</b> & researcher',email='synthetic@example.invalid',department='Test',role='Researcher',orcid_id='0000-0003-1315-5960')).json()
        rid=researcher['id']
        works=[dict(title='Water <irrigation> & field measurements',doi='  https://doi.org/10.1234/ABC ',year=2026,source='orcid'),
               dict(title='Water <irrigation> & field measurements',doi='10.1234/abc',year=2026,source='orcid')]
        with patch('agents.bibliometrie.services.publication_sync.fetch_orcid_works',new=AsyncMock(return_value=works)):
            first=self.client.post(f'/api/biblio/researchers/{rid}/publications/sync')
            self.assertEqual(first.status_code,200,first.text)
            self.assertEqual(first.json()['publications_created'],1)
            second=self.client.post(f'/api/biblio/researchers/{rid}/publications/sync')
            self.assertEqual(second.json()['publications_created'],0)
            self.assertEqual(second.json()['links_created'],0)
        pdf=self.client.get(f'/api/biblio/researchers/{rid}/cv/pdf')
        self.assertEqual(pdf.status_code,200,pdf.text[:100] if pdf.status_code!=200 else '')
        self.assertEqual(pdf.headers['content-type'],'application/pdf')
        self.assertTrue(pdf.content.startswith(b'%PDF-'))
        from agents.bibliometrie.services.cv_generator import _MinimalResearcher
        profile=_MinimalResearcher(dict(indicators=[dict(metric_name='h_index',value=0)]))
        self.assertEqual(profile.h_index,0)
        self.assertIsNone(profile.citation_count)

    def test_missing_abstract_does_not_generate_scientific_claims(self):
        from agents.veille.services.summarizer import summarize_article
        with patch('agents.veille.services.summarizer.llm_client.chat',new=AsyncMock()) as chat:
            result=asyncio.run(summarize_article('Title-only record','',language='en'))
            self.assertIn('Summary unavailable',result)
            chat.assert_not_awaited()

    def test_approval_chain_and_researcher_permissions(self):
        pid=self.parcel()
        self.reading(pid)
        rec=self.until(lambda: self.recommendations(pid))[0]
        self.assertEqual(rec['recommended_irrigation_mm'],42)
        self.assertFalse(rec['is_validated'])
        body=dict(recommendation_id=rec['id'], occurred_at=datetime.utcnow().isoformat(),amount_mm=20,recorded_by='Test operator')
        path=f'/api/twin/parcels/{pid}/irrigation-events'
        self.assertEqual(self.client.post(path,json=body).status_code,409)
        async def researcher(): return User(id='researcher-fixture',role='researcher')
        app.dependency_overrides[get_current_user]=researcher
        approve=f"/api/twin/recommendations/{rec['id']}/approve"
        self.assertEqual(self.client.patch(approve).status_code,403)
        app.dependency_overrides.clear()
        self.assertEqual(self.client.patch(approve).status_code,200)
        self.assertEqual(self.client.post(path,json=body).status_code,200)

    def test_bad_latest_blocks_all_modeling_and_old_approval(self):
        pid=self.parcel()
        self.reading(pid,when=datetime.utcnow()-timedelta(hours=1))
        old=self.until(lambda: self.recommendations(pid))[0]
        bad=self.reading(pid,999)
        self.assertEqual(self.reviewed(pid,bad['id'])['quality_flag'],'error')
        for path, body in [(f'/api/twin/parcels/{pid}/recommend',{}),
                           (f'/api/simulation/parcels/{pid}/runs',{}),
                           (f'/api/optimisation/parcels/{pid}/runs',{})]:
            with self.subTest(path=path):
                response=self.client.post(path,json=body)
                self.assertEqual(response.status_code,400,response.text)
        self.assertEqual(self.client.patch(f"/api/twin/recommendations/{old['id']}/approve").status_code,409)

    def test_pending_ingestion_cannot_be_used_before_validator(self):
        pid=self.parcel()
        with patch('agents.qualite.agent.qualite_agent._validate_twin_reading',new=AsyncMock()):
            reading=self.reading(pid)
            self.assertEqual(reading['quality_flag'],'pending')
            self.assertEqual(reading['review_status'],'pending_validation')
            self.assertEqual(self.client.post(f'/api/twin/parcels/{pid}/recommend').status_code,400)

    def test_demo_stale_and_future_measurements_are_blocked(self):
        for origin, when in [('demo',datetime.utcnow()),('test',datetime.utcnow()),
                             ('field',datetime.utcnow()-timedelta(days=4)),
                             ('field',datetime.utcnow()+timedelta(days=1))]:
            with self.subTest(origin=origin,when=when):
                pid=self.parcel()
                reading=self.reading(pid,origin=origin,when=when)
                self.reviewed(pid,reading['id'])
                self.assertEqual(self.client.post(f'/api/twin/parcels/{pid}/recommend').status_code,400)
                self.assertEqual(self.recommendations(pid),[])

    def test_corrected_measurement_reenters_workflow(self):
        pid=self.parcel()
        bad=self.reading(pid,999)
        self.reviewed(pid,bad['id'])
        review=next(r for r in self.client.get('/api/qualite/measurement-reviews').json() if r['reading_id']==bad['id'])
        path=f"/api/qualite/measurement-reviews/{review['id']}"
        invalid=self.client.patch(path,json=dict(action='correct',correction={'soil_moisture_mm':-1}))
        self.assertEqual(invalid.status_code,422,invalid.text)
        self.assertEqual(self.client.patch(path,json=dict(action='accept')).status_code,422)
        self.assertEqual(self.client.patch(path,json=dict(action='correct',correction={'soil_moisture_mm':999})).status_code,422)
        r=self.client.patch(path,json=dict(action='correct',annotation='Verified unit conversion',correction={'soil_moisture_mm':60}))
        self.assertEqual(r.status_code,200,r.text)
        rec=self.until(lambda:self.recommendations(pid))[0]
        self.assertEqual(rec['source_reading_id'],bad['id'])
        self.assertEqual(rec['recommended_irrigation_mm'],42)

    def test_csv_validates_history_and_rejects_bad_rows(self):
        pid=self.parcel()
        today=datetime.utcnow()
        csv='recorded_at,soil_moisture_mm,rainfall_mm,evapotranspiration_mm\n'
        csv+='\n'.join(f'{(today-timedelta(days=d)).isoformat()},60,0,4' for d in [2,1,0])
        csv+='\nnot-a-date,-1,0,4\n'
        r=self.client.post(f'/api/twin/parcels/{pid}/readings/import',files={'file':('test.csv',csv,'text/csv')})
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual((r.json()['created'],r.json()['rejected']),(3,1))
        rows=self.until(lambda: self._all_imports_reviewed(pid))
        self.assertEqual(len(rows),3)
        self.assertTrue(all(r['quality_flag']=='ok' for r in rows))
        self.until(lambda:self.recommendations(pid))
        self.assertEqual(len(self.recommendations(pid)),1)

    def _all_imports_reviewed(self,pid):
        rows=self.client.get(f'/api/twin/parcels/{pid}/readings').json()
        return rows if len(rows)==3 and all(r['review_status']!='pending_validation' for r in rows) else None

    def test_parcel_domain_validation(self):
        for changes in [dict(area_ha=-1),dict(latitude=999),dict(longitude=-190),
                        dict(field_capacity_mm=40,wilting_point_mm=45),dict(name='  ')]:
            with self.subTest(changes=changes):
                body=dict(name='Fixture',code=str(uuid4()),area_ha=1,latitude=36,longitude=10)
                self.assertEqual(self.client.post('/api/twin/parcels',json={**body,**changes}).status_code,422)

    def test_project_update_validates_dates_status_and_immutable_id(self):
        body=dict(nom='Project fixture',date_debut='2026-01-01',responsable='Test researcher',budget_alloue=100)
        project=self.client.post('/api/mis/projets/',json=body).json()
        path='/api/mis/projets/'+project['id']
        r=self.client.put(path,json=dict(date_fin_prevue='2026-12-01',statut='en_cours',responsable='New owner'))
        self.assertEqual(r.status_code,200,r.text)
        self.assertEqual(r.json()['date_fin_prevue'],'2026-12-01')
        for changes in [dict(date_fin_prevue='2025-01-01'),dict(statut='unknown'),dict(id='changed'),dict(budget_alloue=-1)]:
            self.assertEqual(self.client.put(path,json=changes).status_code,422)
        self.assertEqual(self.client.get(path).json()['statut'],'en_cours')
        self.assertEqual(self.client.put(path,json={'date_fin_prevue':None,'statut':'suspendu'}).status_code,200)
        self.until(lambda: any(r['entite_id']==project['id'] for r in self.client.get('/api/qualite/rapports').json()))

    def test_simulation_and_schedule_with_reviewed_input(self):
        from agents.digitaltwin.services.forecast import ForecastCoverage, WeatherInput
        pid=self.parcel()
        reading=self.reading(pid)
        self.until(lambda:self.recommendations(pid))
        start=datetime.utcnow().date()+timedelta(days=1)
        forecast=ForecastCoverage(inputs=[WeatherInput(0,4,20)]*3,start_date=start,
                                  end_date=start+timedelta(days=2),retrieved_at=datetime.utcnow(),
                                  provider='test-fixture',provider_model='constant-weather')
        with patch('agents.simulation.agent.get_current_forecast_coverage',new=AsyncMock(return_value=forecast)), patch('agents.optimisation.agent.get_current_forecast_coverage',new=AsyncMock(return_value=forecast)):
            sim=self.client.post(f'/api/simulation/parcels/{pid}/runs',json={'horizon_days':3})
            opt=self.client.post(f'/api/optimisation/parcels/{pid}/runs',json={'horizon_days':3,'water_quota_mm':30,'max_irrigation_mm_per_day':15})
        self.assertEqual(sim.status_code,200,sim.text)
        self.assertEqual(opt.status_code,200,opt.text)
        run=opt.json()
        self.assertEqual(run['assumptions']['source_reading_id'],reading['id'])
        self.assertLessEqual(sum(row['irrigation_mm'] for row in run['schedule']),30)
        self.assertTrue(all(row['irrigation_mm']<=15 for row in run['schedule']))
        self.assertEqual(self.client.post(f"/api/optimisation/runs/{run['id']}/approve").status_code,200)

    def test_read_only_role_cannot_write_even_without_specific_route_guard(self):
        import httpx
        from shared.config import settings
        for metadata in [{'lab_role':'viewer'}, {'lab_role':'unknown'}, {}]:
            with self.subTest(metadata=metadata):
                response=httpx.Response(200,json={'id':'fixture-user','app_metadata':metadata})
                with patch.object(settings,'DISABLE_AUTH',False), patch.object(settings,'SUPABASE_URL','https://example.invalid'), patch.object(settings,'SUPABASE_PUBLISHABLE_KEY','fixture'), patch('shared.security.httpx.AsyncClient.get',new=AsyncMock(return_value=response)):
                    headers={'Authorization':'Bearer fixture-token'}
                    self.assertEqual(self.client.get('/api/mis/projets/',headers=headers).status_code,200)
                    r=self.client.post('/api/qualite/valider/projet/fixture',headers=headers)
                    self.assertEqual(r.status_code,403,r.text)

    def test_watch_failure_is_visible_and_not_stamped_success(self):
        async def scenario():
            async with AsyncSessionLocal() as db:
                await db.execute(update(Source).values(active=False))
                source=Source(name='Unavailable test source',url='https://example.invalid/feed',type='rss',active=True)
                db.add(source)
                await db.commit()
                with patch('agents.veille.services.scraper.httpx.AsyncClient.get',new=AsyncMock(side_effect=RuntimeError('offline fixture'))):
                    run=await veille_agent.run_collection(db)
                self.assertEqual(run.status,'failed')
                self.assertIn('offline fixture',run.error_message)
                await db.refresh(source)
                self.assertIsNone(source.last_scraped)
                source.active=False
                await db.commit()
        self.client.portal.call(scenario)

    def test_embedding_failure_is_visible_and_does_not_store_article(self):
        async def scenario():
            async with AsyncSessionLocal() as db:
                await db.execute(update(Source).values(active=False))
                source=Source(name='Enrichment fixture',url='https://example.invalid/feed',type='rss',active=True)
                db.add(source)
                await db.commit()
                item=dict(title='Fixture paper',abstract='Test only',doi=None,authors=[])
                with patch.object(veille_agent,'_fetch_source',new=AsyncMock(return_value=([item],None))), patch('agents.veille.agent.generate_embedding',new=AsyncMock(return_value=[])):
                    run=await veille_agent.run_collection(db)
                self.assertEqual(run.status,'completed_with_warnings')
                self.assertIn('Embedding',run.error_message)
                self.assertEqual(run.articles_collected,0)
                source.active=False
                await db.commit()
        self.client.portal.call(scenario)

    def test_public_boundary_and_private_access(self):
        from shared.config import settings
        with patch.object(settings,'DISABLE_AUTH',False), patch.object(settings,'SUPABASE_URL','https://example.invalid'), patch.object(settings,'SUPABASE_PUBLISHABLE_KEY','fixture'):
            self.assertEqual(self.client.get('/api/public/projects').status_code,200)
            self.assertEqual(self.client.get('/api/mis/projets/').status_code,401)
            self.assertEqual(self.client.get('/api/public/admin/projects').status_code,401)


if __name__=='__main__':
    unittest.main()

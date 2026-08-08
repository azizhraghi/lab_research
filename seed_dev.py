"""seed_dev.py — populate multiagent.db with real rows through the ORM.

Run from repo root (with .venv active):
    python seed_dev.py
"""
import asyncio
import datetime
import json
import os
from uuid import uuid4

from shared.database import AsyncSessionLocal, engine, Base
from agents.veille.models import Source, Article, ArticleTag, ArticleSummary
from agents.bibliometrie.models import (
    Researcher, Publication, ResearcherPublication, BiblioIndicator, CVProfile,
)
from agents.digitaltwin.models import (
    Parcel, SensorReading, IrrigationRecommendation,
    IrrigationEvent, WeatherForecast,
)
from agents.simulation.models import SimulationRun
from agents.optimisation.models import OptimizationRun
from agents.mis.models import Projet, Personnel, Equipement, Budget

RESEARCHERS_FILE = "data/researchers.json"
TODAY = datetime.date.today()
NOW = datetime.datetime.utcnow()


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Clear existing seed data so the script is re-runnable
        from sqlalchemy import text
        for tbl in [
            "veille_alert_notifications", "veille_alert_rules",
            "veille_article_summaries", "veille_article_tags", "veille_articles",
            "veille_sources",
            "biblio_cv_profiles", "biblio_indicators",
            "biblio_researcher_publications", "biblio_publications",
            "biblio_researchers",
            "twin_calibration_profiles", "twin_weather_forecasts",
            "twin_irrigation_events", "twin_recommendations",
            "twin_sensor_readings", "twin_simulations", "twin_parcels",
            "simulation_runs", "optimisation_runs",
            "budgets", "equipements", "personnels", "projets",
        ]:
            await db.execute(text(f"DELETE FROM {tbl}"))
        await db.commit()

        # ── Veille ────────────────────────────────────────────────────
        src1 = Source(name="arXiv cs.AI", type="rss",
                      url="https://arxiv.org/rss/cs.AI", active=True)
        src2 = Source(name="PubMed Bioinformatics", type="rss",
                      url="https://pubmed.ncbi.nlm.nih.gov/rss/search/bioinformatics.xml",
                      active=True)
        db.add_all([src1, src2])
        await db.flush()

        art1 = Article(
            title="Attention Is All You Need",
            abstract="The dominant sequence transduction models are based on complex recurrent or convolutional neural networks.",
            authors=["Vaswani, A.", "Shazeer, N.", "Parmar, N."],
            doi="10.48550/arXiv.1706.03762",
            url="https://arxiv.org/abs/1706.03762",
            source_id=src1.id,
            published_at=datetime.datetime(2017, 6, 12),
        )
        art2 = Article(
            title="BERT: Pre-training of Deep Bidirectional Transformers",
            abstract="We introduce BERT, a new language representation model.",
            authors=["Devlin, J.", "Chang, M.-W.", "Lee, K.", "Toutanova, K."],
            doi="10.48550/arXiv.1810.04805",
            url="https://arxiv.org/abs/1810.04805",
            source_id=src1.id,
            published_at=datetime.datetime(2018, 10, 11),
        )
        art3 = Article(
            title="Deep learning for genomics",
            abstract="Deep learning methods have transformed genomic research.",
            authors=["Zou, J.", "Huss, M."],
            doi="10.1038/s41588-018-0295-5",
            url="https://www.nature.com/articles/s41588-018-0295-5",
            source_id=src2.id,
            published_at=datetime.datetime(2019, 1, 7),
        )
        db.add_all([art1, art2, art3])
        await db.flush()

        db.add_all([
            ArticleTag(article_id=art1.id, tag="transformers", confidence=0.97),
            ArticleTag(article_id=art1.id, tag="attention mechanism", confidence=0.95),
            ArticleTag(article_id=art1.id, tag="NLP", confidence=0.90),
            ArticleTag(article_id=art2.id, tag="NLP", confidence=0.98),
            ArticleTag(article_id=art2.id, tag="pre-training", confidence=0.94),
            ArticleTag(article_id=art2.id, tag="transformers", confidence=0.88),
            ArticleTag(article_id=art3.id, tag="genomics", confidence=0.96),
            ArticleTag(article_id=art3.id, tag="deep learning", confidence=0.93),
        ])

        db.add_all([
            ArticleSummary(article_id=art1.id, language="en", generated_at=NOW,
                           summary_text="Introduces the Transformer, an architecture "
                                        "relying entirely on self-attention and dispensing "
                                        "with recurrence and convolutions. Sets new BLEU "
                                        "records on WMT translation with far less training time."),
            ArticleSummary(article_id=art2.id, language="en", generated_at=NOW,
                           summary_text="Presents BERT, which pre-trains deep bidirectional "
                                        "representations using a masked-language-model objective "
                                        "and achieves state of the art on eleven NLP tasks with "
                                        "minimal task-specific architecture."),
        ])

        # ── Bibliometrie (ORM tables) ─────────────────────────────────
        r1 = Researcher(name="Dr. Amina Benali", email="a.benali@lab.local",
                        department="Computer Science", role="researcher")
        r2 = Researcher(name="Prof. Karim Meziane", email="k.meziane@lab.local",
                        orcid_id="0000-0002-1234-5678",
                        department="Bioinformatics", role="professor")
        db.add_all([r1, r2])
        await db.flush()

        pub1 = Publication(title="Attention Is All You Need", doi="10.48550/arXiv.1706.03762",
                           journal="NeurIPS", year=2017, type="conference",
                           citation_count=90000, source="manual")
        pub2 = Publication(title="BERT: Pre-training of Deep Bidirectional Transformers",
                           doi="10.48550/arXiv.1810.04805",
                           journal="NAACL", year=2019, type="conference",
                           citation_count=55000, source="manual")
        pub3 = Publication(title="Deep learning for genomics",
                           doi="10.1038/s41588-018-0295-5",
                           journal="Nature Genetics", year=2019, type="journal",
                           citation_count=1200, source="manual")
        db.add_all([pub1, pub2, pub3])
        await db.flush()

        db.add_all([
            ResearcherPublication(researcher_id=r1.id, publication_id=pub1.id, author_position=1),
            ResearcherPublication(researcher_id=r1.id, publication_id=pub2.id, author_position=2),
            ResearcherPublication(researcher_id=r2.id, publication_id=pub3.id, author_position=1),
        ])
        db.add_all([
            BiblioIndicator(researcher_id=r1.id, metric_name="h_index", value=12.0, computed_at=NOW),
            BiblioIndicator(researcher_id=r1.id, metric_name="i10_index", value=8.0, computed_at=NOW),
            BiblioIndicator(researcher_id=r1.id, metric_name="total_citations", value=320.0, computed_at=NOW),
            BiblioIndicator(researcher_id=r2.id, metric_name="h_index", value=18.0, computed_at=NOW),
            BiblioIndicator(researcher_id=r2.id, metric_name="i10_index", value=14.0, computed_at=NOW),
            BiblioIndicator(researcher_id=r2.id, metric_name="total_citations", value=890.0, computed_at=NOW),
        ])
        db.add_all([
            CVProfile(researcher_id=r1.id, template="default", custom_sections=[], last_generated=NOW),
            CVProfile(researcher_id=r2.id, template="default", custom_sections=[], last_generated=NOW),
        ])

        # ── Digital Twin ──────────────────────────────────────────────
        p1 = Parcel(name="Parcelle Nord", code="P-NORD-01", crop_type="wheat",
                    area_ha=12.5, latitude=36.72, longitude=3.08,
                    soil_type="clay-loam", field_capacity_mm=130.0, wilting_point_mm=50.0)
        p2 = Parcel(name="Parcelle Sud", code="P-SUD-02", crop_type="corn",
                    area_ha=8.3, latitude=36.68, longitude=3.12,
                    soil_type="sandy-loam", field_capacity_mm=110.0, wilting_point_mm=40.0)
        db.add_all([p1, p2])
        await db.flush()

        for i in range(7):
            dt = NOW - datetime.timedelta(days=i)
            db.add(SensorReading(parcel_id=p1.id, recorded_at=dt,
                                 soil_moisture_mm=95.0 - i * 2,
                                 rainfall_mm=0.0 if i != 3 else 8.5,
                                 evapotranspiration_mm=4.2,
                                 temperature_c=24.0 + i * 0.3,
                                 sensor_code="SNS-01", quality_flag="ok",
                                 data_origin="seed_dev"))
            db.add(SensorReading(parcel_id=p2.id, recorded_at=dt,
                                 soil_moisture_mm=80.0 - i * 1.5,
                                 rainfall_mm=0.0 if i != 3 else 8.5,
                                 evapotranspiration_mm=5.1,
                                 temperature_c=25.0 + i * 0.3,
                                 sensor_code="SNS-02", quality_flag="ok",
                                 data_origin="seed_dev"))

        db.add(IrrigationEvent(parcel_id=p1.id, occurred_at=NOW - datetime.timedelta(days=5),
                               amount_mm=25.0, method="drip", source="field_log",
                               notes="Scheduled irrigation", recorded_by="operator"))
        db.add(IrrigationRecommendation(parcel_id=p1.id, generated_at=NOW,
                                        water_balance_mm=-18.5,
                                        recommended_irrigation_mm=20.0,
                                        confidence=0.82,
                                        rationale="Soil moisture below 80% field capacity; ET forecast high.",
                                        is_validated=False))
        db.add(IrrigationRecommendation(parcel_id=p2.id, generated_at=NOW,
                                        water_balance_mm=-12.0,
                                        recommended_irrigation_mm=15.0,
                                        confidence=0.75,
                                        rationale="Moderate deficit; sandy soil drains faster.",
                                        is_validated=False))

        for d in range(5):
            fdate = TODAY + datetime.timedelta(days=d)
            db.add(WeatherForecast(parcel_id=p1.id, forecast_date=fdate,
                                   issued_at=NOW, precipitation_mm=2.0 * d,
                                   et0_fao_mm=4.5, temperature_mean_c=23.0 + d,
                                   precipitation_probability_pct=20.0 + d * 5,
                                   source_metadata={"provider_run": "seed_dev"}))

        # ── Simulation ────────────────────────────────────────────────
        db.add(SimulationRun(
            parcel_id=p1.id, created_at=NOW,
            scenario_name="Drought stress +2°C",
            horizon_days=14,
            rainfall_factor=0.6, et_factor=1.2, temperature_delta_c=2.0,
            initial_moisture_mm=90.0,
            baseline_summary={"total_irrigation_mm": 60.0, "final_balance_mm": -5.0},
            scenario_summary={"total_irrigation_mm": 85.0, "final_balance_mm": -22.0},
            deltas={"irrigation_delta_mm": 25.0, "balance_delta_mm": -17.0},
            time_series=[{"day": i, "moisture_mm": 90.0 - i * 1.5} for i in range(14)],
            assumptions={"model": "FAO-56", "seed": "seed_dev"},
        ))

        # ── Optimisation ──────────────────────────────────────────────
        db.add(OptimizationRun(
            parcel_id=p1.id, created_at=NOW,
            run_name="Water-quota 200mm / 14d",
            horizon_days=14,
            max_irrigation_mm_per_day=15.0,
            water_quota_mm=200.0,
            rainfall_factor=1.0, et_factor=1.0, temperature_delta_c=0.0,
            constraints={"max_per_day_mm": 15.0, "total_quota_mm": 200.0},
            summary={"total_applied_mm": 168.0, "deficit_days": 2},
            schedule=[{"day": i, "irrigation_mm": 12.0 if i % 3 == 0 else 0.0} for i in range(14)],
            assumptions={"model": "LP", "seed": "seed_dev"},
        ))

        # ── MIS ───────────────────────────────────────────────────────
        proj_id = str(uuid4())
        db.add(Projet(id=proj_id, nom="Plateforme IA Labo",
                      description="Développement de la plateforme multi-agents de recherche.",
                      statut="en_cours",
                      date_debut=datetime.date(2025, 1, 15),
                      date_fin_prevue=datetime.date(2026, 12, 31),
                      budget_alloue=150000.0, responsable="Prof. Karim Meziane"))
        proj2_id = str(uuid4())
        db.add(Projet(id=proj2_id, nom="Jumeau Numérique Agricole",
                      description="Modélisation et simulation des parcelles irriguées.",
                      statut="planifie",
                      date_debut=datetime.date(2026, 3, 1),
                      date_fin_prevue=datetime.date(2027, 6, 30),
                      budget_alloue=80000.0, responsable="Dr. Amina Benali"))

        pers_id = str(uuid4())
        db.add(Personnel(id=pers_id, nom="Benali", prenom="Amina",
                         email="a.benali@lab.local", role="researcher",
                         competences="Python, ML, NLP", disponible=True,
                         projet_actuel_id=proj_id))
        db.add(Personnel(id=str(uuid4()), nom="Meziane", prenom="Karim",
                         email="k.meziane@lab.local", role="professor",
                         competences="Bioinformatics, Statistics", disponible=True,
                         projet_actuel_id=proj_id))

        equip_id = str(uuid4())
        db.add(Equipement(id=equip_id, nom="Serveur GPU A100",
                          type="computing", etat="operationnel",
                          localisation="Salle serveurs B12",
                          responsable_id=pers_id,
                          date_acquisition=datetime.date(2024, 6, 1),
                          valeur_estimee=45000.0))
        db.add(Equipement(id=str(uuid4()), nom="Station météo IoT",
                          type="sensor", etat="operationnel",
                          localisation="Parcelle Nord",
                          date_acquisition=datetime.date(2024, 9, 15),
                          valeur_estimee=3200.0))

        db.add(Budget(id=str(uuid4()), projet_id=proj_id,
                      montant_alloue=150000.0, montant_depense=62400.0,
                      devise="EUR",
                      date_debut=datetime.date(2025, 1, 15),
                      date_fin=datetime.date(2026, 12, 31),
                      description="Budget principal plateforme IA"))
        db.add(Budget(id=str(uuid4()), projet_id=proj2_id,
                      montant_alloue=80000.0, montant_depense=0.0,
                      devise="EUR",
                      date_debut=datetime.date(2026, 3, 1),
                      description="Budget jumeau numérique"))

        await db.commit()
        print("DB seeded")

    # ── data/researchers.json (bibliometrie agent in-memory store) ────
    os.makedirs("data", exist_ok=True)
    profiles = {
        "Dr. Amina Benali": {
            "id": str(uuid4()),
            "name": "Dr. Amina Benali",
            "email": "a.benali@lab.local",
            "orcid": None,
            "google_scholar_id": None,
            "publications": [
                {"id": str(uuid4()), "title": "Attention Is All You Need",
                 "topic": "NLP", "source": "manual",
                 "discovered_at": "2017-06-12T00:00:00+00:00"},
                {"id": str(uuid4()), "title": "BERT: Pre-training of Deep Bidirectional Transformers",
                 "topic": "NLP", "source": "manual",
                 "discovered_at": "2018-10-11T00:00:00+00:00"},
            ],
            "h_index": 12,
            "citation_count": 320,
            "topics": ["NLP", "transformers", "deep learning"],
            "last_updated": NOW.isoformat() + "+00:00",
        },
        "Prof. Karim Meziane": {
            "id": str(uuid4()),
            "name": "Prof. Karim Meziane",
            "email": "k.meziane@lab.local",
            "orcid": "0000-0002-1234-5678",
            "google_scholar_id": None,
            "publications": [
                {"id": str(uuid4()), "title": "Deep learning for genomics",
                 "topic": "bioinformatics", "source": "manual",
                 "discovered_at": "2019-01-07T00:00:00+00:00"},
            ],
            "h_index": 18,
            "citation_count": 890,
            "topics": ["genomics", "bioinformatics", "deep learning"],
            "last_updated": NOW.isoformat() + "+00:00",
        },
    }
    with open(RESEARCHERS_FILE, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2, ensure_ascii=False)
    print(f"{RESEARCHERS_FILE} written ({len(profiles)} profiles)")


if __name__ == "__main__":
    asyncio.run(seed())

# Research Lab Agents

Système multi-agents pour la gestion d'un laboratoire de recherche.
Construit avec **FastAPI**, **SQLAlchemy 2.0**, **PostgreSQL** et **Docker**.

---

## Architecture générale

Le système est composé de trois agents principaux :

| Agent | Rôle | Statut |
|---|---|---|
| **MIS** (Management Information System) | Gestion des données : projets, personnel, équipements, budgets | Complet |
| **Orchestrateur** | Coordination et routage des événements entre agents | Complet |
| **Qualité** | Validation des données et conformité RGPD | Complet |

---

## Stack technique

- **FastAPI** — framework API async
- **SQLAlchemy 2.0** — ORM async (syntaxe `Mapped[]`)
- **asyncpg** — driver PostgreSQL asynchrone
- **PostgreSQL 16** — base de données relationnelle (via Docker)
- **Docker Desktop** — conteneurisation de la base de données
- **Pydantic v2** — validation des schémas API
- **python-dotenv** — gestion des variables d'environnement
- **Mistral AI SDK** — évaluation qualité par LLM (agent Qualité)
- **Apache Kafka** — bus d'événements distribué (implémentation alternative de l'EventBus)
- **Redis** — bus d'événements pub/sub léger (implémentation alternative de l'EventBus)

---

## Prérequis

- Python 3.13+
- Docker Desktop (en cours d'exécution)
- Git
- Clé API Mistral (gratuite sur console.mistral.ai)
- Docker doit avoir assez de ressources pour Kafka en plus de PostgreSQL (RAM recommandée : 4 Go+)

---

## Installation

### 1. Cloner le dépôt

```bash
git clone https://github.com/wassiLabsx/research-lab-agents.git
cd research-lab-agents
```

### 2. Créer et activer l'environnement virtuel

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Créer le fichier `.env`

Crée un fichier `.env` à la racine du projet :
DATABASE_URL=postgresql+asyncpg://mis_user:mis_password@localhost:5432/mis_db
POSTGRES_USER=mis_user
POSTGRES_PASSWORD=mis_password
POSTGRES_DB=mis_db
MISTRAL_API_KEY=ta_clé_mistral
EVENT_BUS_TYPE=memory
> Ce fichier n'est pas versionné (listé dans `.gitignore`).

### 5. Lancer PostgreSQL via Docker

```bash
docker compose up -d
```

Vérifie que le conteneur tourne :

```bash
docker ps
# mis_postgres  Up  0.0.0.0:5432->5432/tcp
```

### 6. Créer les tables SQL

```bash
python create_tables.py
```

### 7. Lancer le serveur

```bash
uvicorn app.main:app --reload
```

L'API est disponible sur : http://127.0.0.1:8000
Documentation Swagger : http://127.0.0.1:8000/docs

---

## Structure du projet

```
research-lab-agents/
├── app/
│   ├── agents/
│   │   ├── mis_agent.py              # Agent MIS (logique métier + événements)
│   │   ├── orchestrateur_agent.py    # Orchestrateur (15 règles métier)
│   │   └── qualite_agent.py          # Agent Qualité (validation + RGPD)
│   ├── core/
│   │   ├── base_agent.py             # Classe abstraite BaseAgent
│   │   └── event_bus.py              # EventBus (interface) + InMemoryEventBus + KafkaEventBus + RedisEventBus
│   ├── models/
│   │   └── mis.py                    # Modèles SQLAlchemy (tables SQL)
│   ├── routers/
│   │   ├── mis.py                    # 20 endpoints CRUD
│   │   ├── orchestrateur.py          # 5 endpoints Orchestrateur
│   │   └── qualite.py                # 8 endpoints Qualité
│   ├── schemas/
│   │   ├── events.py                 # Schémas Pydantic : Event, AgentAction
│   │   ├── mis.py                    # Schémas : Projet, Personnel, Equipement, Budget
│   │   ├── orchestrateur.py          # Schémas : Alerte, HistoriqueEvenement
│   │   └── qualite.py                # Schémas : RapportQualite, DemandeValidation
│   ├── services/
│   │   └── llm_client.py            # Client Mistral : évaluation IA + décisions de routage
│   ├── database.py                   # Connexion SQLAlchemy async + session + Base
│   ├── main.py                       # Point d'entrée FastAPI + lifespan
│   └── state.py                      # Instances partagées des 3 agents
├── .env                              # Variables d'environnement (non versionné)
├── docker-compose.yml                # PostgreSQL 16 + volume persistant
├── requirements.txt
├── test_base_agent.py
├── scripts_dev/
│   ├── test_mistral.py
│   └── test_llm_client.py
├── test_event_bus.py
└── README.md
```
---

## API — Endpoints disponibles

### MIS — Projets
| Méthode | Route | Description |
|---|---|---|
| `POST` | `/projets/` | Créer un projet |
| `GET` | `/projets/` | Lister tous les projets |
| `GET` | `/projets/{id}` | Obtenir un projet |
| `PUT` | `/projets/{id}` | Modifier un projet |
| `DELETE` | `/projets/{id}` | Supprimer un projet |

### MIS — Personnel
| Méthode | Route | Description |
|---|---|---|
| `POST` | `/personnels/` | Créer un membre |
| `GET` | `/personnels/` | Lister le personnel |
| `GET` | `/personnels/{id}` | Obtenir un membre |
| `PUT` | `/personnels/{id}` | Modifier un membre |
| `DELETE` | `/personnels/{id}` | Supprimer un membre |

### MIS — Equipements
| Méthode | Route | Description |
|---|---|---|
| `POST` | `/equipements/` | Créer un équipement |
| `GET` | `/equipements/` | Lister les équipements |
| `GET` | `/equipements/{id}` | Obtenir un équipement |
| `PUT` | `/equipements/{id}` | Modifier un équipement |
| `DELETE` | `/equipements/{id}` | Supprimer un équipement |

### MIS — Budgets
| Méthode | Route | Description |
|---|---|---|
| `POST` | `/budgets/` | Créer un budget |
| `GET` | `/budgets/` | Lister les budgets |
| `GET` | `/budgets/{id}` | Obtenir un budget |
| `PUT` | `/budgets/{id}` | Modifier un budget |
| `DELETE` | `/budgets/{id}` | Supprimer un budget |

### Orchestrateur
| Méthode | Route | Description |
|---|---|---|
| `GET` | `/orchestrateur/status` | Statut + stats de l'agent |
| `GET` | `/orchestrateur/alertes` | Liste des alertes actives/résolues |
| `GET` | `/orchestrateur/historique` | Historique des événements traités |
| `GET` | `/orchestrateur/decisions-ia` | Décisions de routage IA (fallback Mistral) |
| `POST` | `/orchestrateur/trigger` | Déclencher manuellement un événement |
| `PATCH` | `/orchestrateur/alertes/{id}/resoudre` | Résoudre une alerte |

### Qualité
| Méthode | Route | Description |
|---|---|---|
| `GET` | `/qualite/status` | Statut + stats de l'agent |
| `GET` | `/qualite/rapports` | Tous les rapports générés |
| `GET` | `/qualite/rapports/{entite_id}` | Rapports pour une entité |
| `POST` | `/qualite/valider/projet/{id}` | Valider un projet |
| `POST` | `/qualite/valider/personnel/{id}` | Valider un personnel (+ RGPD) |
| `POST` | `/qualite/valider/equipement/{id}` | Valider un équipement |
| `POST` | `/qualite/valider/budget/{id}` | Valider un budget |
| `POST` | `/qualite/valider` | Valider via EventBus |
| `POST` | `/qualite/evaluation-ia` | Évaluation qualité par IA (Mistral) |

---

## Communication inter-agents (EventBus)

Les agents communiquent via un pattern **publish/subscribe** sur l'`EventBus`.
Convention de nommage : `nom_agent.ce_qui_s_est_passe`

```python
await event_bus.publish(Event(
    type="simulation.terminee",
    source_agent="agent_simulation",
    payload={"simulation_id": "sim-001", "resultat": "succes"}
))
```

### Evenements supportés

| Source | Evenement | Action Orchestrateur |
|---|---|---|
| MIS | `projet.created` | Vérifie responsable + budget |
| MIS | `budget.depense` | Alerte si >80% ou >100% |
| MIS | `equipement.etat_change` | Notifie si maintenance |
| Veille | `veille.article_trouve` | Notifie chercheurs |
| Simulation | `simulation.terminee` | Déclenche Optimisation |
| Optimisation | `optimisation.contrainte_violee` | Alerte critique |
| Qualité | `qualite.anomalie_detectee` | Suspend projet |
| Qualité | `qualite.validation_ok` | Marque conforme RGPD |

---

## Phases du projet

- Phase 0 — Fondations : BaseAgent, EventBus, schémas Pydantic partagés — Complet
- Phase 1 — MIS Agent : 20 endpoints CRUD, stockage en mémoire — Complet
- Phase 2 — PostgreSQL : migration vers une vraie base de données persistante — Complet
- Phase 3 — Orchestrateur : 15 règles métier, alertes, historique — Complet
- Phase 4 — Agent Qualité : validation RGPD, variables d'environnement — Complet
- Phase 5 — Intégration LLM : évaluation qualité par IA via Mistral API, sortie JSON structurée — Complet (mode standalone, branchement PostgreSQL en cours)
- Phase 6 — Fallback IA Orchestrateur : décision de routage par LLM pour les événements hors des 15 règles connues, avec liste fermée d'agents et double vérification anti-hallucination — Complet
- Phase 7 — EventBus Kafka : implémentation KafkaEventBus interchangeable avec InMemoryEventBus via configuration (.env), infrastructure Docker en mode KRaft — Complet
- Phase 8 — EventBus Redis : implémentation RedisEventBus (pub/sub) comme troisième option interchangeable via .env — Complet
---
## Bus d'événements (EventBus)

Le système supporte trois implémentations interchangeables de l'`EventBus`, sélectionnables via la variable `EVENT_BUS_TYPE` dans `.env` :

| Valeur | Implémentation | Usage recommandé |
|---|---|---|
| `memory` (défaut) | `InMemoryEventBus` | Développement local, tests rapides, démonstration |
| `kafka` | `KafkaEventBus` | Architecture distribuée, persistance et replay des événements |
| `redis` | `RedisEventBus` | Pub/sub léger et rapide, sans persistance |

Les trois implémentations respectent la même interface abstraite (`publish`, `subscribe`), donc aucun agent ne nécessite de modification lors du changement d'implémentation.

Le service Kafka est disponible via Docker (mode KRaft, sans Zookeeper) sur le port `9092`.
Le service Redis est disponible via Docker (image `redis:7-alpine`) sur le port `6379`.
--- 

## Base de données

| Paramètre | Valeur |
|---|---|
| Image | `postgres:16` |
| Conteneur | `mis_postgres` |
| Base | `mis_db` (depuis `.env`) |
| Port | `5432` |
| Volume | `postgres_data` (persistant) |

Les credentials sont définis dans le fichier `.env` non versionné.
En production, utiliser un gestionnaire de secrets dédié.

---

## Auteur

**WBS** — Projet multi-agents académique
Stack : FastAPI · SQLAlchemy 2.0 · PostgreSQL · Docker · Python 3.13
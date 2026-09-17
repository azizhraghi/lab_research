> Archive: this August 2026 capability report is superseded by README.md and docs/IMPROVEMENTS-2026-09-08.md. Its operation count, tests, agent behavior and pending features are historical, not current verification.

# LRSTE — Capacités réelles de la plateforme et feuille de route

**Date : août 2026 · Audience : direction du laboratoire · Statut : vérifié**

Ce document décrit ce que la plateforme fait **réellement** aujourd'hui, ce
qu'elle **n'est pas**, et les décisions qui restent à prendre. Chaque
affirmation de la première partie a été vérifiée en conditions réelles (API
démarrée, requêtes exécutées, chaînes d'événements tracées) — rien ici n'est
aspirational.

---

## 1. Ce qui fonctionne — vérifié de bout en bout

### Veille scientifique (littérature)
- Collecte depuis **RSS/Atom, ArXiv et PubMed** (requêtes de recherche
  configurables par source).
- Chaque article collecté est **dédupliqué par vecteur sémantique** (Mistral
  Embed, 1024 dimensions ; index HNSW prêt pour Postgres/pgvector), **taggé par
  IA** et **résumé en français et en anglais**.
- Un article porteur d'un DOI dont un auteur correspond à un chercheur du labo
  est **automatiquement rattaché à son profil** de publications.

### Bibliométrie
- **79 opérations API** au total sur la plateforme. Profils chercheurs avec
  identifiants ORCID / Google Scholar / Scopus.
- **Métriques** (h-index, citations) via une chaîne de repli réelle :
  Google Scholar → Scopus (si clé API) → Semantic Scholar → OpenAlex.
- **Import de publications** depuis ORCID et Google Scholar — dédupliqué par
  DOI normalisé, idempotent, lignes partagées entre co-auteurs.
- **CV en PDF** généré à partir des données réelles (indicateurs +
  publications importées).

### Jumeau numérique des parcelles irriguées — la boucle eau complète
C'est le cœur métier. **Toute la chaîne est opérable depuis l'interface :**

1. **Saisie des mesures terrain** (capteurs d'humidité du sol, pluie, ET,
   température) — manuelle ou import CSV.
2. **Contrôle qualité automatique** : chaque mesure reçoit un verdict calculé
   — `ok` / `suspect` / `erreur` — basé sur des plausibilités physiques
   (humidité négative impossible, au-delà de la saturation suspecte, hausse
   d'humidité sans eau arrivée = application non journalisée, etc.).
   **Seules les mesures `ok` alimentent les conseils automatiques.**
3. **Recommandation d'irrigation** (bilan hydrique FAO-56) — générée
   automatiquement à chaque mesure validée, **mais jamais appliquée sans
   approbation humaine**.
4. **Journalisation des irrigations réellement effectuées**, rattachées à la
   recommandation qu'elles exécutent.
5. **Calibration** : ajustement du coefficient cultural et de la capacité au
   champ par recherche sur grille, avec RMSE et **divulguée honnêtement** — si
   le sol ne s'est jamais saturé dans la fenêtre, le profil le dit au lieu de
   prétendre une calibration complète.
6. **Prévisions météo** Open-Meteo (fournisseur et modèle tracés),
   **simulation de scénarios** (facteurs pluie/ET/température) et
   **optimisation** de calendrier d'irrigation sous quota (ordonnanceur glouton
   à contraintes).

### Gestion du laboratoire (MIS)
- Projets, personnel, équipements, budgets — création, édition, suppression
  **gardée** (refus avec compte des dépendances plutôt qu'une cascade qui
  détruirait des mesures ou des liens bibliographiques).
- La création d'un projet déclenche une alerte « mettre en place la parcelle »
  côté jumeau numérique, avec création pré-remplie depuis le tableau de bord.

### Orchestrateur et qualité
- **15 règles de routage** d'événements ; historique et alertes **persistés en
  base** ; alertes contextualisées avec actions concrètes.
- **Planification de tâches** : heuristique déterministe à contraintes
  (compétences, disponibilité, état des équipements, conflits d'occupation) —
  **signale explicitement les blocages** (« aucune personne disponible avec la
  compétence X ») au lieu de forcer une affectation ; chaque proposition
  exige une approbation humaine.
- Agent qualité : validation des projets/budgets/personnel/équipements +
  contrôle physique des mesures terrain (ci-dessus).

### Socle technique
- FastAPI asynchrone, 8 agents dont **6 connectés au bus d'événements** avec
  des chaînes réelles (mesure → validation → recommandation → approbation →
  application → résolution d'alerte).
- Authentification Supabase avec rôles (viewer / researcher / reviewer /
    administrator) appliqués côté API.
- Migrations Alembic versionnées ; dépendances épinglées (lockfile).

---

## 2. Ce que la plateforme N'EST PAS — à lire avant de communiquer

Le cahier des charges initial décrit une plateforme multi-années multi-équipes.
L'implémentation actuelle est un **MVP fonctionnel et honnête**, pas cette
plateforme. En particulier :

| Promis dans le cahier | Réalité | Écart |
|---|---|---|
| Wrappers SWAT / HEC-HMS / EPANET / WEAP / MODFLOW | **Bilan hydrique FAO-56 mono-zone** — l'un des quatre moteurs nommés par le cahier lui-même (ligne 95), et le bon pour des parcelles irriguées | Majeur : pas de bassin versant, pas de réseau hydraulique |
| Optimisation bayésienne / algorithmes génétiques | Ordonnanceur glouton à contraintes | Moyen — mais déterministe, explicable, et suffisant pour un quota d'irrigation |
| Django + PostGIS | FastAPI + SQLite (dev) | Architectural — fonctionne, mais à faire évoluer pour la prod |
| Kafka + Celery | Bus Redis Streams / Kafka / mémoire — code présent, **non validé en déploiement** ; Celery supprimé (code mort) | Moyen |
| Keycloak (OIDC, 2FA) | Supabase Auth (JWT + rôles) | Moyen |
| MinIO, MLflow/DVC, Parquet+DuckDB, Grafana | Absents | Majeur |
| Conformité RGPD complète | Contrôles de complétude des données | Majeur — politique à définir |
| Modules thèses, SIG, jeux de données, événements, actualités | Pages « non implémenté » affichant la raison | Assumé et affiché honnêtement |

**Recommandation : re-étiqueter le cahier plutôt que promettre des moteurs.**
Intégrer réellement SWAT ou EPANET représente des mois ; le bilan FAO-56
calibré est l'outil correct pour les *parcelles irriguées* — c'est une
décision de crédibilité, pas de technique.

---

## 3. Limites opérationnelles connues (août 2026)

1. **SQLite en développement** — mono-écrivain. La migration pgvector est
   prête mais n'a jamais tourné contre un vrai Postgres. À faire avant toute
   utilisation multi-utilisateur simultanée.
2. **Bus en mémoire** — le dispatch est désormais asynchrone (hors du chemin
   des requêtes HTTP), mais mono-processus : un redémarrage perd les événements
   en transit. Redis Streams est le passage à l'échelle prévu.
3. **`DISABLE_AUTH`** doit rester `false` hors développement local.
4. **Aucun test automatisé** — les vérifications sont manuelles et
   reproductibles (documentées dans HANDOFF.md), mais une suite de tests est
   nécessaire avant une dépendance quotidienne du laboratoire.

---

## 4. Feuille de route recommandée

**Court terme (semaines) — fiabiliser**
1. Déploiement Postgres + validation de toute la chaîne de migrations
   (pgvector/HNSW inclus).
2. Interface sensible aux rôles (masquer les boutons interdits plutôt que
   403 au clic).
3. Suite de tests automatisés sur les chaînes critiques (eau + publications).

**Moyen terme (1–2 mois) — passer à l'échelle**
4. Redis Streams en production + workers pour les récupérations longues
   (Scholar, ORCID).
5. Endpoint d'ingestion capteur (API authentifiée pour passerelles IoT) —
   le contrôle qualité existe déjà.
6. Automatisations MIS (rappels, dépassements budget/livrables) sur le
   modèle de la planification : déterministe, contraintes signalées,
   approbation humaine.

**Décision stratégique — à trancher par la direction**
7. **Moteurs hydrologiques** : soit un cas d'usage concret justifie EPANET
   (réseaux — librairie `wntr` intégrable) ou SWAT+ (bassin versant), soit le
   cahier est re-étiqueté « jumeau numérique de parcelles irriguées FAO-56 » —
   ce qu'il est réellement et qui rend déjà service.
8. **Politique RGPD** : consentement, conservation, anonymisation — à définir
   avec les outils existants comme socle.

---

*Chaque affirmation de la partie 1 est reproductible : voir HANDOFF.md pour les
procédures de vérification et l'historique des sessions.*

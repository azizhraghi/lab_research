// Mirrors the Pydantic response models in agents/*/schemas.py.
// Dates are ISO strings (the API returns them serialized).

export interface ArticleTag {
  tag: string;
  confidence?: number | null;
}

export interface ArticleSummary {
  language: string;
  summary_text: string;
  generated_at: string;
}

export interface Article {
  id: number;
  source_id: number;
  title: string;
  abstract?: string | null;
  authors?: string[] | null;
  doi?: string | null;
  url?: string | null;
  published_at?: string | null;
  collected_at: string;
  tags: ArticleTag[];
  summaries: ArticleSummary[];
}

export interface Source {
  id: number;
  name: string;
  type: string;
  url: string;
  config?: Record<string, unknown> | null;
  active: boolean;
  last_scraped?: string | null;
}

export interface Parcel {
  id: number;
  name: string;
  code: string;
  crop_type: string;
  area_ha: number;
  latitude: number;
  longitude: number;
  soil_type: string;
  field_capacity_mm: number;
  wilting_point_mm: number;
  created_at: string;
}

export interface SensorReading {
  id: number;
  recorded_at: string;
  soil_moisture_mm: number;
  rainfall_mm: number;
  evapotranspiration_mm: number;
  temperature_c?: number | null;
  quality_flag: string;
  data_origin: string;
}

export interface Recommendation {
  id: number;
  generated_at: string;
  recommended_irrigation_mm: number;
  water_balance_mm: number;
  confidence: number;
  rationale: string;
  is_validated: boolean;
}

export interface ParcelDetail extends Parcel {
  latest_readings: SensorReading[];
  latest_recommendations: Recommendation[];
}

export interface WeatherForecast {
  id: number;
  parcel_id: number;
  forecast_date: string;
  issued_at: string;
  retrieved_at: string;
  provider: string;
  provider_model: string;
  precipitation_mm: number;
  et0_fao_mm: number;
  temperature_mean_c?: number | null;
  precipitation_probability_pct?: number | null;
  source_metadata: Record<string, unknown>;
}

export interface SimulationRun {
  id: number;
  parcel_id: number;
  created_at: string;
  scenario_name: string;
  horizon_days: number;
  rainfall_factor: number;
  et_factor: number;
  temperature_delta_c: number;
  initial_moisture_mm?: number | null;
  baseline_summary: Record<string, unknown>;
  scenario_summary: Record<string, unknown>;
  deltas: Record<string, unknown>;
  time_series: Record<string, unknown>[];
  assumptions: Record<string, unknown>;
}

// ── Bibliométrie ──────────────────────────────────────────────────────

export interface Indicator {
  metric_name: string;
  value: number;
  computed_at: string;
}

export interface CVProfile {
  template: string;
  custom_sections: Record<string, unknown>[];
  last_generated?: string | null;
}

export interface Researcher {
  id: number;
  name: string;
  email: string;
  orcid_id?: string | null;
  scholar_id?: string | null;
  scopus_id?: string | null;
  department: string;
  role: string;
  indicators: Indicator[];
  cv_profile?: CVProfile | null;
}

export interface ResearcherCreate {
  name: string;
  email: string;
  orcid_id?: string | null;
  scholar_id?: string | null;
  scopus_id?: string | null;
  department: string;
  role: string;
}

export interface Publication {
  id: number;
  title: string;
  abstract?: string | null;
  doi?: string | null;
  journal?: string | null;
  year?: number | null;
  type?: string | null;
  source: string;
  citation_count: number;
}

// ── MIS ───────────────────────────────────────────────────────────────

export type ProjetStatut = "planifie" | "en_cours" | "termine" | "suspendu";
export type RolePersonnel = "chercheur" | "ingenieur" | "technicien" | "administratif" | "doctorant";
export type EtatEquipement = "operationnel" | "en_maintenance" | "indisponible";

export interface Projet {
  id: string;
  nom: string;
  description?: string | null;
  statut: ProjetStatut;
  date_debut: string;
  date_fin_prevue?: string | null;
  budget_alloue: number;
  responsable: string;
}

export interface Personnel {
  id: string;
  nom: string;
  prenom: string;
  email: string;
  role: RolePersonnel;
  competences: string[];
  disponible: boolean;
  projet_actuel_id?: string | null;
}

export interface Equipement {
  id: string;
  nom: string;
  type: string;
  etat: EtatEquipement;
  localisation: string;
  responsable_id?: string | null;
  date_acquisition?: string | null;
  valeur_estimee: number;
}

export interface Budget {
  id: string;
  projet_id: string;
  montant_alloue: number;
  montant_depense: number;
  devise: string;
  date_debut: string;
  date_fin?: string | null;
  description?: string | null;
}

// ── Qualité ───────────────────────────────────────────────────────────

export type NiveauQualite = "conforme" | "avertissement" | "non_conforme";

export interface RapportQualite {
  id: string;
  entite_type: string;
  entite_id: string;
  niveau: NiveauQualite;
  problemes: string[];
  timestamp: string;
  conforme_rgpd: boolean;
}

// ── Orchestrateur ─────────────────────────────────────────────────────

export type NiveauAlerte = "info" | "orange" | "rouge" | "critique";

export interface Alerte {
  id: string;
  niveau: NiveauAlerte;
  message: string;
  source_evenement: string;
  timestamp: string;
  resolue: boolean;
}

export interface HistoriqueEvenement {
  id: string;
  type_evenement: string;
  source_agent: string;
  payload: Record<string, unknown>;
  timestamp: string;
  traite: boolean;
  alertes_generees: string[];
}

export interface OrchestratorStatus {
  agent: string;
  statut: string;
  evenements_traites: number;
  alertes_actives: number;
  alertes_resolues: number;
  regles_actives: number;
}

export interface OptimizationRun {
  id: number;
  parcel_id: number;
  created_at: string;
  run_name: string;
  horizon_days: number;
  max_irrigation_mm_per_day: number;
  water_quota_mm?: number | null;
  rainfall_factor: number;
  et_factor: number;
  temperature_delta_c: number;
  constraints: Record<string, unknown>;
  summary: Record<string, unknown>;
  schedule: Record<string, unknown>[];
  assumptions: Record<string, unknown>;
}

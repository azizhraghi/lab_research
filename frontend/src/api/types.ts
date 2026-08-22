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
  project_id?: string | null;
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

/**
 * Shape returned by GET /api/twin/parcels/{id}/readings — SensorReadingResponse
 * in agents/digitaltwin/schemas.py, which adds two fields the inline shape
 * embedded on ParcelDetail does not carry.
 */
export interface SensorReadingFull extends SensorReading {
  parcel_id: number;
  sensor_code: string;
}

/**
 * Water actually applied to a parcel. Calibration sums these per day into the
 * water balance it fits against, so a missing event silently biases the fit.
 */
export interface IrrigationEvent {
  id: number;
  parcel_id: number;
  recommendation_id?: number | null;
  occurred_at: string;
  amount_mm: number;
  method: string;
  source: string;
  notes?: string | null;
  recorded_by: string;
  created_at: string;
}

/**
 * Fitted water-balance parameters. The server column is a free-form JSON dict,
 * so these are the keys `create_calibration_candidate` actually writes
 * (agents/digitaltwin/services/calibration.py:126-133) rather than a contract
 * Pydantic enforces.
 */
export interface CalibrationParameters {
  /** Fitted Kc. Reaches simulation/optimisation via get_active_crop_coefficient,
   *  but NOT /recommend, which reads the static CROP_COEFFICIENTS table. */
  crop_coefficient: number;
  /** The only parameter `apply` writes back onto the parcel. */
  field_capacity_mm: number;
  wilting_point_mm: number;
  /** The crop's FAO-56 value before fitting — the multiplier baseline. */
  base_crop_coefficient: number;
  calibration_method: string;
  irrigation_timing_assumption: string;
}

/** Fit error against the withheld daily observations. Lower is better; bias
 *  shows direction (positive = the model predicts wetter than measured). */
export interface CalibrationMetrics {
  mae_mm: number;
  rmse_mm: number;
  bias_mm: number;
  /** One fewer than observation_count — the first day seeds the balance. */
  validation_observations: number;
}

export interface CalibrationDataQuality {
  observation_count: number;
  calendar_days: number;
  coverage_pct: number;
  /** Events inside the window. Zero on an irrigated parcel means the fit is
   *  explaining away applied water as rainfall or a wrong Kc. */
  irrigation_event_count: number;
  measurement_requirement: string;
  accepted_data_origins: string[];
  weather_inputs: string;
  status: string;
}

/** candidate → applied; applying supersedes whatever was previously applied. */
export type CalibrationStatus = "candidate" | "applied" | "superseded";

export interface CalibrationProfile {
  id: number;
  parcel_id: number;
  created_at: string;
  source_start_date: string;
  source_end_date: string;
  status: CalibrationStatus;
  parameters: CalibrationParameters;
  metrics: CalibrationMetrics;
  data_quality: CalibrationDataQuality;
  reviewed_by?: string | null;
  applied_at?: string | null;
}

export interface Recommendation {
  id: number;
  source_reading_id?: number | null;
  generation_mode?: string;
  generated_at: string;
  recommended_irrigation_mm: number;
  water_balance_mm: number;
  confidence: number;
  rationale: string;
  is_validated: boolean;
  validated_by?: string | null;
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

/** Outcome of POST /api/biblio/researchers/{id}/publications/sync.
 *
 * The counts answer different questions and are worth showing separately:
 * `works_found` is what ORCID holds, `publications_created` is what was new to
 * the lab, and `links_created` is what was new to *this* researcher. A
 * co-author's sync typically reports created 0 / links 1 — the paper was
 * already on file, the authorship was not. */
export interface OrcidSyncResult {
  researcher_id: number;
  source: string;
  orcid_id: string;
  works_found: number;
  publications_created: number;
  publications_enriched: number;
  links_created: number;
  links_already_present: number;
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
  context: Record<string, unknown>;
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

export type PlanningTaskPriority = "low" | "normal" | "high" | "critical";
export type PlanningTaskStatus = "pending" | "planned" | "in_progress" | "completed";

export interface PlanningTask {
  id: string;
  title: string;
  description?: string | null;
  project_id?: string | null;
  priority: PlanningTaskPriority;
  status: PlanningTaskStatus;
  due_date?: string | null;
  duration_hours: number;
  required_skills: string[];
  required_equipment_ids: string[];
  assigned_personnel_id?: string | null;
  scheduled_start?: string | null;
  scheduled_end?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PlanningProposal {
  id: string;
  status: "proposed" | "approved" | "discarded";
  proposed_assignments: Array<{
    task_id: string;
    title: string;
    personnel_id: string;
    personnel_name: string;
    equipment_ids: string[];
    scheduled_start: string;
    scheduled_end: string;
    rationale: string;
  }>;
  conflicts: Array<{ task_id: string; title: string; reasons: string[] }>;
  created_at: string;
  approved_at?: string | null;
  approved_by?: string | null;
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

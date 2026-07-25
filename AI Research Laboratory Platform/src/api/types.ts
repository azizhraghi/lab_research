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

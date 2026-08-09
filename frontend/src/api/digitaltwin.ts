import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../lib/apiClient";
import type {
  OptimizationRun,
  Parcel,
  ParcelDetail,
  Recommendation,
  SensorReadingFull,
  SimulationRun,
  WeatherForecast,
} from "./types";

export function useParcels() {
  return useQuery<Parcel[]>({
    queryKey: ["twin", "parcels"],
    queryFn: () => apiFetch<Parcel[]>("/api/twin/parcels"),
  });
}

/**
 * Body accepted by POST /api/twin/parcels — mirrors ParcelCreate in
 * agents/digitaltwin/schemas.py. crop_type, soil_type, field_capacity_mm and
 * wilting_point_mm have server-side defaults, so they are optional here.
 * Note the route is guarded by require_roles("administrator").
 */
export interface ParcelCreate {
  name: string;
  code: string;
  area_ha: number;
  latitude: number;
  longitude: number;
  crop_type?: string;
  soil_type?: string;
  field_capacity_mm?: number;
  wilting_point_mm?: number;
}

export function useCreateParcel() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: ParcelCreate) =>
      apiFetch<Parcel>("/api/twin/parcels", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["twin", "parcels"] }),
  });
}

export function useParcel(id?: number | null) {
  return useQuery<ParcelDetail>({
    queryKey: ["twin", "parcel", id],
    queryFn: () => apiFetch<ParcelDetail>(`/api/twin/parcels/${id}`),
    enabled: Boolean(id),
  });
}

export function useParcelForecast(id?: number | null, days = 16) {
  return useQuery<WeatherForecast[]>({
    queryKey: ["twin", "forecast", id, days],
    queryFn: () =>
      apiFetch<WeatherForecast[]>(`/api/twin/parcels/${id}/forecasts?days=${days}`),
    enabled: Boolean(id),
  });
}

export function useRefreshForecast() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      apiFetch(`/api/twin/parcels/${id}/forecasts/refresh`, { method: "POST" }),
    onSuccess: (_data, id) => {
      qc.invalidateQueries({ queryKey: ["twin", "forecast", id] });
      qc.invalidateQueries({ queryKey: ["twin", "parcel", id] });
    },
  });
}

/**
 * Body accepted by POST /api/twin/parcels/{id}/readings — mirrors
 * SensorReadingCreate in agents/digitaltwin/schemas.py. Guarded by
 * require_roles("researcher", "reviewer", "administrator").
 *
 * `recorded_at` must be a NAIVE ISO string ("2026-08-08T06:00") — an offset or
 * trailing Z shifts the value and breaks the import upsert's equality check.
 * `data_origin` is deliberately not exposed: the server default "field" is
 * correct for manual entry, and the CSV route forces "field_import".
 */
export interface SensorReadingCreate {
  recorded_at: string;
  /** Root-zone water STORAGE in mm, not volumetric %. ge=0, no upper bound. */
  soil_moisture_mm: number;
  rainfall_mm?: number;
  /** Reference ET0. The crop coefficient is applied server-side. */
  evapotranspiration_mm?: number;
  /** Stored on the row but never read by the water-balance model. */
  temperature_c?: number | null;
  /** Part of the CSV upsert key (parcel_id, recorded_at, sensor_code). */
  sensor_code?: string;
  /** Only the exact string "ok" is eligible for calibration. */
  quality_flag?: string;
}

/** Result of POST /api/twin/parcels/{id}/readings/import. */
export interface SensorReadingImportResult {
  parcel_id: number;
  created: number;
  updated: number;
  rejected: number;
  /** Server caps this at the first 20 entries while `rejected` counts them all. */
  errors: string[];
}

/**
 * GET /api/twin/parcels/{id}/readings — newest first, server limit is 1..365.
 * Prefer this over ParcelDetail.latest_readings, which the server caps at 30.
 */
export function useReadings(id?: number | null, limit = 90) {
  return useQuery<SensorReadingFull[]>({
    queryKey: ["twin", "readings", id, limit],
    queryFn: () =>
      apiFetch<SensorReadingFull[]>(
        `/api/twin/parcels/${id}/readings?limit=${limit}`,
      ),
    enabled: Boolean(id),
  });
}

export function useCreateReading() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      parcelId,
      body,
    }: {
      parcelId: number;
      body: SensorReadingCreate;
    }) =>
      apiFetch<SensorReadingFull>(`/api/twin/parcels/${parcelId}/readings`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: (_data, { parcelId }) => {
      qc.invalidateQueries({ queryKey: ["twin", "readings", parcelId] });
      qc.invalidateQueries({ queryKey: ["twin", "parcel", parcelId] });
    },
  });
}

/**
 * Bulk CSV import. The multipart field name must be exactly "file".
 * apiFetch omits Content-Type for FormData so the browser can set the
 * multipart boundary itself.
 */
export function useImportReadings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ parcelId, file }: { parcelId: number; file: File }) => {
      const form = new FormData();
      form.append("file", file);
      return apiFetch<SensorReadingImportResult>(
        `/api/twin/parcels/${parcelId}/readings/import`,
        { method: "POST", body: form },
      );
    },
    onSuccess: (_data, { parcelId }) => {
      qc.invalidateQueries({ queryKey: ["twin", "readings", parcelId] });
      qc.invalidateQueries({ queryKey: ["twin", "parcel", parcelId] });
    },
  });
}

/** Result of DELETE /api/twin/parcels/{id}/readings/{readingId}. */
export interface SensorReadingDeleteResult {
  parcel_id: number;
  deleted_id: number;
  recorded_at: string;
  /**
   * True when the removed row was the newest by recorded_at — i.e. the one
   * /recommend was reading. Any recommendation already stored keeps the old
   * figure, so the UI should prompt for a re-run.
   */
  was_latest: boolean;
  /** Readings left on the parcel; 0 means /recommend will now 400. */
  remaining: number;
}

/**
 * DELETE /api/twin/parcels/{id}/readings/{readingId} — the correction path for a
 * mistyped measurement. Scoped to the parcel server-side, so a reading id from
 * another parcel 404s rather than deleting across parcels. Guarded by
 * require_roles("researcher", "reviewer", "administrator").
 */
export function useDeleteReading() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      parcelId,
      readingId,
    }: {
      parcelId: number;
      readingId: number;
    }) =>
      apiFetch<SensorReadingDeleteResult>(
        `/api/twin/parcels/${parcelId}/readings/${readingId}`,
        { method: "DELETE" },
      ),
    onSuccess: (_data, { parcelId }) => {
      qc.invalidateQueries({ queryKey: ["twin", "readings", parcelId] });
      qc.invalidateQueries({ queryKey: ["twin", "parcel", parcelId] });
    },
  });
}

/**
 * POST /api/twin/parcels/{id}/recommend — takes no request body. Uses only the
 * single most recent reading by recorded_at, so back-dating a reading does not
 * change the result. Returns 400 (not 404) when the parcel has no readings.
 */
export function useRecommend() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (parcelId: number) =>
      apiFetch<Recommendation & { parcel_id: number }>(
        `/api/twin/parcels/${parcelId}/recommend`,
        { method: "POST" },
      ),
    onSuccess: (_data, parcelId) => {
      qc.invalidateQueries({ queryKey: ["twin", "parcel", parcelId] });
    },
  });
}

/** Run the digital-twin scenario simulation (POST /api/twin/parcels/{id}/simulate). */
export function useRunTwinSimulation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      apiFetch(`/api/twin/parcels/${id}/simulate`, {
        method: "POST",
        body: JSON.stringify({}),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["twin"] }),
  });
}

export function useSimulationRuns(parcelId?: number | null) {
  return useQuery<SimulationRun[]>({
    queryKey: ["simulation", "runs", parcelId],
    queryFn: () =>
      apiFetch<SimulationRun[]>(`/api/simulation/parcels/${parcelId}/runs`),
    enabled: Boolean(parcelId),
  });
}

/**
 * Scenario parameters accepted by POST /api/simulation/parcels/{id}/runs.
 * Mirrors SimulationRunRequest in agents/simulation/schemas.py — the ranges in
 * the comments are the server-side Field constraints, so the UI must not exceed
 * them or the request is rejected with a 422.
 */
export interface SimulationParams {
  scenario_name?: string;
  horizon_days?: number;        // 3 … 16
  rainfall_factor?: number;     // 0 … 3
  et_factor?: number;           // 0 … 3
  temperature_delta_c?: number; // -10 … 15
  initial_moisture_mm?: number | null;
}

export function useRunSimulation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ parcelId, params }: { parcelId: number; params?: SimulationParams }) =>
      apiFetch<SimulationRun>(`/api/simulation/parcels/${parcelId}/runs`, {
        method: "POST",
        body: JSON.stringify(params ?? {}),
      }),
    onSuccess: (_data, { parcelId }) =>
      qc.invalidateQueries({ queryKey: ["simulation", "runs", parcelId] }),
  });
}

export function useOptimisationRuns(parcelId?: number | null) {
  return useQuery<OptimizationRun[]>({
    queryKey: ["optimisation", "runs", parcelId],
    queryFn: () =>
      apiFetch<OptimizationRun[]>(`/api/optimisation/parcels/${parcelId}/runs`),
    enabled: Boolean(parcelId),
  });
}

export function useRunOptimisation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (parcelId: number) =>
      apiFetch(`/api/optimisation/parcels/${parcelId}/runs`, {
        method: "POST",
        body: JSON.stringify({}),
      }),
    onSuccess: (_data, parcelId) =>
      qc.invalidateQueries({ queryKey: ["optimisation", "runs", parcelId] }),
  });
}

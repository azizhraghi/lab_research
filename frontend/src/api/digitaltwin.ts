import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../lib/apiClient";
import type {
  OptimizationRun,
  Parcel,
  ParcelDetail,
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

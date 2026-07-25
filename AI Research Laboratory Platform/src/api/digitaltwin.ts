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

export function useRunSimulation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (parcelId: number) =>
      apiFetch(`/api/simulation/parcels/${parcelId}/runs`, {
        method: "POST",
        body: JSON.stringify({}),
      }),
    onSuccess: (_data, parcelId) =>
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

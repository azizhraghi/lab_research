import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../lib/apiClient";
import type { Alerte, HistoriqueEvenement, OrchestratorStatus } from "./types";

export function useOrchestratorStatus() {
  return useQuery<OrchestratorStatus>({
    queryKey: ["orch", "status"],
    queryFn: () => apiFetch<OrchestratorStatus>("/api/orchestrateur/status"),
  });
}

export function useAlertes(resolues = false) {
  return useQuery<Alerte[]>({
    queryKey: ["orch", "alertes", resolues],
    queryFn: () =>
      apiFetch<Alerte[]>(`/api/orchestrateur/alertes?resolues=${resolues}`),
  });
}

export function useHistorique() {
  return useQuery<HistoriqueEvenement[]>({
    queryKey: ["orch", "historique"],
    queryFn: () => apiFetch<HistoriqueEvenement[]>("/api/orchestrateur/historique"),
  });
}

export function useResolveAlerte() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (alerteId: string) =>
      apiFetch(`/api/orchestrateur/alertes/${alerteId}/resoudre`, { method: "PATCH" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["orch", "alertes"] }),
  });
}

export function useTriggerEvent() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { type: string; source_agent: string; payload: Record<string, unknown> }) =>
      apiFetch("/api/orchestrateur/trigger", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["orch", "historique"] });
      qc.invalidateQueries({ queryKey: ["orch", "alertes"] });
    },
  });
}

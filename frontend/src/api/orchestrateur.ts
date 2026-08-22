import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../lib/apiClient";
import type { Alerte, HistoriqueEvenement, OrchestratorStatus, PlanningProposal, PlanningTask } from "./types";

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

export type PlanningTaskCreate = Pick<PlanningTask,
  "title" | "description" | "project_id" | "priority" | "due_date" |
  "duration_hours" | "required_skills" | "required_equipment_ids"
>;

export function usePlanningTasks() {
  return useQuery<PlanningTask[]>({
    queryKey: ["orch", "planning", "tasks"],
    queryFn: () => apiFetch<PlanningTask[]>("/api/orchestrateur/planning/tasks"),
  });
}

export function useCreatePlanningTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: PlanningTaskCreate) =>
      apiFetch<PlanningTask>("/api/orchestrateur/planning/tasks", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["orch", "planning"] });
      qc.invalidateQueries({ queryKey: ["orch", "historique"] });
    },
  });
}

export function usePlanningProposals() {
  return useQuery<PlanningProposal[]>({
    queryKey: ["orch", "planning", "proposals"],
    queryFn: () => apiFetch<PlanningProposal[]>("/api/orchestrateur/planning/proposals"),
  });
}

export function useGeneratePlanningProposal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => apiFetch<PlanningProposal>("/api/orchestrateur/planning/proposals", { method: "POST" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["orch", "planning"] });
      qc.invalidateQueries({ queryKey: ["orch", "historique"] });
    },
  });
}

export function useApprovePlanningProposal() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (proposalId: string) =>
      apiFetch<PlanningProposal>(`/api/orchestrateur/planning/proposals/${proposalId}/approve`, { method: "PATCH" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["orch", "planning"] });
      qc.invalidateQueries({ queryKey: ["orch", "historique"] });
    },
  });
}

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../lib/apiClient";
import type {
  Projet, Personnel, Equipement, Budget, ProjectMilestone, ProjectDeliverable,
  ProjectRisk, BudgetSummary, OperationalAlert, MonthlyProjectReport,
  EquipmentReservation, EquipmentMaintenance, Workload,
} from "./types";

// ── Projets ───────────────────────────────────────────────────────────

export function useProjets() {
  return useQuery<Projet[]>({
    queryKey: ["mis", "projets"],
    queryFn: () => apiFetch<Projet[]>("/api/mis/projets/"),
  });
}

export function useCreateProjet() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Omit<Projet, "id"> & { id?: string }) =>
      apiFetch<Projet>("/api/mis/projets/", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["mis", "projets"] });
      qc.invalidateQueries({ queryKey: ["orch", "alertes"] });
      qc.invalidateQueries({ queryKey: ["orch", "historique"] });
    },
  });
}

export function useUpdateProjet() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Omit<Projet, "id">> }) =>
      apiFetch<Projet>(`/api/mis/projets/${id}`, { method: "PUT", body: JSON.stringify(data) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["mis"] });
      qc.invalidateQueries({ queryKey: ["orch"] });
    },
  });
}

export function useDeleteProjet() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiFetch(`/api/mis/projets/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["mis", "projets"] }),
  });
}

// ── Personnel ─────────────────────────────────────────────────────────

export function usePersonnels() {
  return useQuery<Personnel[]>({
    queryKey: ["mis", "personnels"],
    queryFn: () => apiFetch<Personnel[]>("/api/mis/personnels/"),
  });
}

export function useCreatePersonnel() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Omit<Personnel, "id"> & { id?: string }) =>
      apiFetch<Personnel>("/api/mis/personnels/", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["mis"] }),
  });
}

// ── Équipements ───────────────────────────────────────────────────────

export function useEquipements() {
  return useQuery<Equipement[]>({
    queryKey: ["mis", "equipements"],
    queryFn: () => apiFetch<Equipement[]>("/api/mis/equipements/"),
  });
}

export function useCreateEquipement() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Omit<Equipement, "id"> & { id?: string }) =>
      apiFetch<Equipement>("/api/mis/equipements/", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["mis", "equipements"] }),
  });
}

// ── Budgets ───────────────────────────────────────────────────────────

export function useBudgets() {
  return useQuery<Budget[]>({
    queryKey: ["mis", "budgets"],
    queryFn: () => apiFetch<Budget[]>("/api/mis/budgets/"),
  });
}

export function useCreateBudget() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Omit<Budget, "id"> & { id?: string }) =>
      apiFetch<Budget>("/api/mis/budgets/", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["mis", "budgets"] }),
  });
}

// ── Laboratory operations ────────────────────────────────────────────

function invalidateProjectOperations(qc: ReturnType<typeof useQueryClient>, projectId?: string) {
  qc.invalidateQueries({ queryKey: ["mis", "operational-alerts"] });
  qc.invalidateQueries({ queryKey: ["mis", "workload"] });
  qc.invalidateQueries({ queryKey: ["orch", "alertes"] });
  if (projectId) qc.invalidateQueries({ queryKey: ["mis", "project-operations", projectId] });
}

export function useProjectMilestones(projectId?: string) {
  return useQuery<ProjectMilestone[]>({
    queryKey: ["mis", "project-operations", projectId, "milestones"],
    enabled: !!projectId,
    queryFn: () => apiFetch(`/api/mis/projets/${projectId}/milestones`),
  });
}

export function useCreateMilestone(projectId?: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { title: string; due_date: string; owner_id?: string; notes?: string }) =>
      apiFetch<ProjectMilestone>(`/api/mis/projets/${projectId}/milestones`, { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => invalidateProjectOperations(qc, projectId),
  });
}

export function useUpdateMilestone(projectId?: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...body }: { id: string; status?: "pending" | "at_risk" | "completed" }) =>
      apiFetch<ProjectMilestone>(`/api/mis/milestones/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    onSuccess: () => invalidateProjectOperations(qc, projectId),
  });
}

export function useProjectDeliverables(projectId?: string) {
  return useQuery<ProjectDeliverable[]>({
    queryKey: ["mis", "project-operations", projectId, "deliverables"],
    enabled: !!projectId,
    queryFn: () => apiFetch(`/api/mis/projets/${projectId}/deliverables`),
  });
}

export function useCreateDeliverable(projectId?: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { title: string; deliverable_type?: string; due_date?: string; owner_id?: string }) =>
      apiFetch<ProjectDeliverable>(`/api/mis/projets/${projectId}/deliverables`, { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => invalidateProjectOperations(qc, projectId),
  });
}

export function useProjectRisks(projectId?: string) {
  return useQuery<ProjectRisk[]>({
    queryKey: ["mis", "project-operations", projectId, "risks"],
    enabled: !!projectId,
    queryFn: () => apiFetch(`/api/mis/projets/${projectId}/risks`),
  });
}

export function useCreateRisk(projectId?: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { title: string; likelihood: number; impact: number; mitigation?: string }) =>
      apiFetch<ProjectRisk>(`/api/mis/projets/${projectId}/risks`, { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => invalidateProjectOperations(qc, projectId),
  });
}

export function useBudgetSummary(budgetId?: string) {
  return useQuery<BudgetSummary>({
    queryKey: ["mis", "budget-summary", budgetId],
    enabled: !!budgetId,
    queryFn: () => apiFetch(`/api/mis/budgets/${budgetId}/summary`),
  });
}

export function useCreateBudgetEntry(projectId?: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { budget_id: string; entry_type: "line" | "commitment" | "expense"; category: string; description: string; amount: number; occurred_at: string }) =>
      apiFetch("/api/mis/budgets/entries", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["mis", "budget-summary"] });
      qc.invalidateQueries({ queryKey: ["mis", "budget-entries"] });
      invalidateProjectOperations(qc, projectId);
    },
  });
}

export function useOperationalAlerts() {
  return useQuery<OperationalAlert[]>({
    queryKey: ["mis", "operational-alerts"],
    queryFn: () => apiFetch("/api/mis/operational-alerts"),
    refetchInterval: 60_000,
  });
}

export function useMonthlyProjectReport(projectId?: string, month?: string) {
  return useQuery<MonthlyProjectReport>({
    queryKey: ["mis", "project-operations", projectId, "monthly-report", month],
    enabled: !!projectId,
    queryFn: () => apiFetch(`/api/mis/projets/${projectId}/monthly-report${month ? `?month=${month}` : ""}`),
  });
}

export function useReservations() {
  return useQuery<EquipmentReservation[]>({
    queryKey: ["mis", "reservations"],
    queryFn: () => apiFetch<EquipmentReservation[]>("/api/mis/reservations"),
  });
}

export function useCreateReservation(projectId?: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { equipment_id: string; project_id?: string; purpose: string; start_at: string; end_at: string }) =>
      apiFetch<EquipmentReservation>("/api/mis/reservations", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["mis", "reservations"] }); invalidateProjectOperations(qc, projectId); },
  });
}

export function useApproveReservation(projectId?: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiFetch<EquipmentReservation>(`/api/mis/reservations/${id}/approve`, { method: "POST" }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["mis", "reservations"] }); invalidateProjectOperations(qc, projectId); },
  });
}

export function useMaintenance() {
  return useQuery<EquipmentMaintenance[]>({
    queryKey: ["mis", "maintenance"],
    queryFn: () => apiFetch<EquipmentMaintenance[]>("/api/mis/maintenance"),
  });
}

export function useCreateMaintenance(projectId?: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { equipment_id: string; maintenance_type: string; due_date: string; notes?: string }) =>
      apiFetch<EquipmentMaintenance>("/api/mis/maintenance", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["mis", "maintenance"] }); invalidateProjectOperations(qc, projectId); },
  });
}

export function useWorkload() {
  return useQuery<Workload[]>({
    queryKey: ["mis", "workload"],
    queryFn: () => apiFetch<Workload[]>("/api/mis/workload"),
  });
}

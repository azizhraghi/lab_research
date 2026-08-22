import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../lib/apiClient";
import type { Projet, Personnel, Equipement, Budget } from "./types";

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
    onSuccess: () => qc.invalidateQueries({ queryKey: ["mis", "personnels"] }),
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

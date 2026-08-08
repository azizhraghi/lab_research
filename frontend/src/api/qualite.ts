import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../lib/apiClient";
import type { RapportQualite } from "./types";

/** Mirrors QualiteAgent.get_stats() — see agents/qualite/agent.py. */
export interface QualiteStatus {
  agent: string;
  statut: string;
  total_rapports: number;
  conformes: number;
  avertissements: number;
  non_conformes: number;
}

export function useQualiteStatus() {
  return useQuery<QualiteStatus>({
    queryKey: ["qualite", "status"],
    queryFn: () => apiFetch<QualiteStatus>("/api/qualite/status"),
  });
}

export function useRapports() {
  return useQuery<RapportQualite[]>({
    queryKey: ["qualite", "rapports"],
    queryFn: () => apiFetch<RapportQualite[]>("/api/qualite/rapports"),
  });
}

/** Entity families the agent knows how to validate. */
export type QualiteEntite = "projet" | "personnel" | "equipement" | "budget";

/**
 * POST /api/qualite/valider/{entite}/{id} — the agent re-reads the row from the
 * MIS tables and returns a fresh report, which it also appends to its history.
 */
export function useValiderEntite() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ entite, id }: { entite: QualiteEntite; id: string }) =>
      apiFetch<RapportQualite>(`/api/qualite/valider/${entite}/${id}`, { method: "POST" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["qualite", "rapports"] });
      qc.invalidateQueries({ queryKey: ["qualite", "status"] });
    },
  });
}

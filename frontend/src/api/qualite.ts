import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../lib/apiClient";
import type { MeasurementReview, RapportQualite } from "./types";

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

export function useMeasurementReviews(status = "pending") {
  return useQuery<MeasurementReview[]>({
    queryKey: ["qualite", "measurement-reviews", status],
    queryFn: () => apiFetch<MeasurementReview[]>(`/api/qualite/measurement-reviews?status=${status}`),
  });
}

export function useDecideMeasurementReview() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ reviewId, action, annotation, correction }: {
      reviewId: string; action: "accept" | "reject" | "annotate" | "correct";
      annotation?: string; correction?: Record<string, unknown>;
    }) => apiFetch<MeasurementReview>(`/api/qualite/measurement-reviews/${reviewId}`, {
      method: "PATCH", body: JSON.stringify({ action, annotation, correction }),
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["qualite", "measurement-reviews"] });
      qc.invalidateQueries({ queryKey: ["twin", "readings"] });
      qc.invalidateQueries({ queryKey: ["twin", "parcel"] });
    },
  });
}

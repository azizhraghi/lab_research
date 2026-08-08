import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../lib/apiClient";
import type { Researcher, ResearcherCreate } from "./types";

export function useResearchers() {
  return useQuery<Researcher[]>({
    queryKey: ["biblio", "researchers"],
    queryFn: () => apiFetch<Researcher[]>("/api/biblio/researchers"),
  });
}

export function useSyncResearcher() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      apiFetch(`/api/biblio/researchers/${id}/sync`, { method: "POST" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["biblio", "researchers"] }),
  });
}

export function useCreateResearcher() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: ResearcherCreate) =>
      apiFetch<Researcher>("/api/biblio/researchers", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["biblio", "researchers"] }),
  });
}

export function useResearcherCvUrl(id: number) {
  return `/api/biblio/researchers/${id}/cv/pdf`;
}

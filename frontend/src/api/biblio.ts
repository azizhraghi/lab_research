import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../lib/apiClient";
import type {
  OrcidSyncResult,
  Publication,
  Researcher,
  ResearcherCreate,
} from "./types";

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

/** The publications linked to one researcher, newest first.
 *
 * `enabled` lets a caller hold the request until a researcher is actually
 * selected — the route 404s on an unknown id rather than returning `[]`, so
 * firing it with a placeholder id would surface a spurious error. */
export function useResearcherPublications(id: number | null) {
  return useQuery<Publication[]>({
    queryKey: ["biblio", "researchers", id, "publications"],
    queryFn: () =>
      apiFetch<Publication[]>(`/api/biblio/researchers/${id}/publications`),
    enabled: id !== null,
  });
}

/** Import a researcher's works from their public ORCID record.
 *
 * Distinct from `useSyncResearcher`, which refreshes h-index and citation
 * counts from Scholar. This one populates the publication list itself, and is
 * the only writer the lab has for that table. Idempotent — re-running matches
 * on DOI and adds only what is new. */
export function useSyncPublications() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      apiFetch<OrcidSyncResult>(
        `/api/biblio/researchers/${id}/publications/sync`,
        { method: "POST" },
      ),
    onSuccess: (_data, id) => {
      qc.invalidateQueries({
        queryKey: ["biblio", "researchers", id, "publications"],
      });
    },
  });
}

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../lib/apiClient";
import type {
  OrcidSyncResult,
  Publication,
  Researcher,
  ResearcherCreate,
  ResearcherUpdate,
  ScholarSyncResult,
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

/** Partial update — only the fields present in the body change. A UNIQUE
 * collision (email or an external id) comes back as a 409 naming the field. */
export function useUpdateResearcher() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...body }: ResearcherUpdate & { id: number }) =>
      apiFetch<Researcher>(`/api/biblio/researchers/${id}`, {
        method: "PUT",
        body: JSON.stringify(body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["biblio", "researchers"] }),
  });
}

/** Delete a researcher. The server refuses with 409 while publications remain
 * linked, so the error message is what the user needs to read. */
export function useDeleteResearcher() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      apiFetch<{ deleted_id: number; name: string }>(`/api/biblio/researchers/${id}`, {
        method: "DELETE",
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
 * counts. This one populates the publication list itself. Idempotent —
 * re-running matches on DOI and adds only what is new. */
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

/** Import publications from a researcher's public Google Scholar profile.
 *
 * Fills the same table as the ORCID import (same DOI dedup), and additionally
 * refreshes citation counts — Scholar is the source that reports them. Expect a
 * 400 with the reason if Scholar blocks the unproxied request. */
export function useSyncScholarPublications() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) =>
      apiFetch<ScholarSyncResult>(
        `/api/biblio/researchers/${id}/publications/sync/scholar`,
        { method: "POST" },
      ),
    onSuccess: (_data, id) => {
      qc.invalidateQueries({
        queryKey: ["biblio", "researchers", id, "publications"],
      });
      qc.invalidateQueries({ queryKey: ["biblio", "researchers"] });
    },
  });
}

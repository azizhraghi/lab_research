import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../lib/apiClient";
import type { PublicDataset, PublicProject, PublicPublication, PublicResearcher } from "./types";

/** Anonymous, approval-controlled API. Do not substitute internal agent hooks here. */
export function usePublicResearchers() {
  return useQuery<PublicResearcher[]>({ queryKey: ["public", "researchers"], queryFn: () => apiFetch("/api/public/researchers") });
}

export function usePublicPublications() {
  return useQuery<PublicPublication[]>({ queryKey: ["public", "publications"], queryFn: () => apiFetch("/api/public/publications") });
}

export function usePublicProjects() {
  return useQuery<PublicProject[]>({ queryKey: ["public", "projects"], queryFn: () => apiFetch("/api/public/projects") });
}

export function usePublicDatasets() {
  return useQuery<PublicDataset[]>({ queryKey: ["public", "datasets"], queryFn: () => apiFetch("/api/public/datasets") });
}

type CurationStatus = "draft" | "published" | "withdrawn";
type CuratedProject = Omit<PublicProject, "status"> & { status: CurationStatus };
type CuratedDataset = Omit<PublicDataset, "status"> & { status: CurationStatus };

function refreshPublic(qc: ReturnType<typeof useQueryClient>) {
  qc.invalidateQueries({ queryKey: ["public"] });
}

export function useCuratedProjects() {
  return useQuery<CuratedProject[]>({ queryKey: ["public", "admin", "projects"], queryFn: () => apiFetch("/api/public/admin/projects") });
}

export function useSubmitPublicProject() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { project_id: string; summary: string; research_area?: string; status?: CurationStatus }) => apiFetch<CuratedProject>("/api/public/admin/projects", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => refreshPublic(qc),
  });
}

export function useSetPublicProjectStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: CurationStatus }) => apiFetch<CuratedProject>(`/api/public/admin/projects/${id}`, { method: "PATCH", body: JSON.stringify({ status }) }),
    onSuccess: () => refreshPublic(qc),
  });
}

export function useCuratedDatasets() {
  return useQuery<CuratedDataset[]>({ queryKey: ["public", "admin", "datasets"], queryFn: () => apiFetch("/api/public/admin/datasets") });
}

export function useSubmitPublicDataset() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { title: string; description: string; version: string; license: string; access_url?: string; keywords?: string[]; status?: CurationStatus }) => apiFetch<CuratedDataset>("/api/public/admin/datasets", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => refreshPublic(qc),
  });
}

export function useSetPublicDatasetStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: CurationStatus }) => apiFetch<CuratedDataset>(`/api/public/admin/datasets/${id}`, { method: "PATCH", body: JSON.stringify({ status }) }),
    onSuccess: () => refreshPublic(qc),
  });
}

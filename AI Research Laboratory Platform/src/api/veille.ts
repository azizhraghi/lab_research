import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../lib/apiClient";
import type { Article, Source } from "./types";

export function useArticles() {
  return useQuery<Article[]>({
    queryKey: ["veille", "articles"],
    queryFn: () => apiFetch<Article[]>("/api/veille/articles"),
  });
}

export function useSources() {
  return useQuery<Source[]>({
    queryKey: ["veille", "sources"],
    queryFn: () => apiFetch<Source[]>("/api/veille/sources"),
  });
}

export function useTriggerScrape() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => apiFetch<{ status: string }>("/api/veille/trigger", { method: "POST" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["veille", "articles"] });
      qc.invalidateQueries({ queryKey: ["veille", "sources"] });
    },
  });
}

export function useCreateSource() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { name: string; type: string; url: string }) =>
      apiFetch<Source>("/api/veille/sources", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["veille", "sources"] }),
  });
}

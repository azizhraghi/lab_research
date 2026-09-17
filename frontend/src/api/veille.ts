import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../lib/apiClient";
import type { Article, CollectionRun, Source, WatchDigest, WatchSubscription } from "./types";

export interface ArticleFilters {
  search?: string;
  tag?: string;
  state?: "all" | "unread" | "read" | "saved" | "shared";
}

export function useArticles(filters: ArticleFilters = {}) {
  const query = new URLSearchParams();
  if (filters.search) query.set("search", filters.search);
  if (filters.tag) query.set("tag", filters.tag);
  if (filters.state && filters.state !== "all") query.set("state", filters.state);
  return useQuery<Article[]>({
    queryKey: ["veille", "articles", filters],
    queryFn: () => apiFetch<Article[]>(`/api/veille/articles${query.size ? `?${query}` : ""}`),
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
    mutationFn: () => apiFetch<CollectionRun>("/api/veille/trigger", { method: "POST" }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["veille", "articles"] });
      qc.invalidateQueries({ queryKey: ["veille", "sources"] });
      qc.invalidateQueries({ queryKey: ["veille", "runs"] });
      qc.invalidateQueries({ queryKey: ["veille", "inbox"] });
    },
  });
}

export function useCreateSource() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { name: string; type: string; url: string; config?: Record<string, unknown>; active?: boolean }) =>
      apiFetch<Source>("/api/veille/sources", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["veille", "sources"] }),
  });
}

export function useDeleteSource() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiFetch<{ deleted_id: number; name: string; type: string }>(`/api/veille/sources/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["veille", "sources"] }),
  });
}

export function useWatchSubscriptions() {
  return useQuery<WatchSubscription[]>({
    queryKey: ["veille", "subscriptions"],
    queryFn: () => apiFetch<WatchSubscription[]>("/api/veille/subscriptions"),
  });
}

export function useCreateWatchSubscription() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: Pick<WatchSubscription, "keywords" | "themes" | "frequency" | "active">) =>
      apiFetch<WatchSubscription>("/api/veille/subscriptions", { method: "POST", body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["veille", "subscriptions"] }),
  });
}

export function useUpdateWatchSubscription() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...body }: Partial<Pick<WatchSubscription, "keywords" | "themes" | "frequency" | "active">> & { id: number }) =>
      apiFetch<WatchSubscription>(`/api/veille/subscriptions/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["veille", "subscriptions"] }),
  });
}

export function useDeleteWatchSubscription() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => apiFetch<void>(`/api/veille/subscriptions/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["veille", "subscriptions"] }),
  });
}

export function useWatchInbox() {
  return useQuery<WatchDigest[]>({
    queryKey: ["veille", "inbox"],
    queryFn: () => apiFetch<WatchDigest[]>("/api/veille/inbox"),
  });
}

export function useUpdateArticleState() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ articleId, ...body }: { articleId: number; is_saved?: boolean; mark_read?: boolean; mark_shared?: boolean; share_note?: string }) =>
      apiFetch<Article>(`/api/veille/articles/${articleId}/state`, { method: "PATCH", body: JSON.stringify(body) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["veille", "articles"] });
      qc.invalidateQueries({ queryKey: ["veille", "inbox"] });
    },
  });
}

export function useCollectionRuns() {
  return useQuery<CollectionRun[]>({
    queryKey: ["veille", "runs"],
    queryFn: () => apiFetch<CollectionRun[]>("/api/veille/runs"),
  });
}

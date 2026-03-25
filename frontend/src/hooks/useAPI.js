/**
 * SWR-based hooks for data fetching with caching and revalidation.
 */

import useSWR from "swr";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const fetcher = (url) => fetch(`${API_BASE}${url}`).then((r) => r.json());

export function useDocuments(params = {}) {
  const query = new URLSearchParams(params).toString();
  return useSWR(`/api/documents?${query}`, fetcher, { refreshInterval: 60000 });
}

export function useDocument(id) {
  return useSWR(id ? `/api/documents/${encodeURIComponent(id)}` : null, fetcher);
}

export function useDocumentStats(release) {
  const query = release ? `?release=${release}` : "";
  return useSWR(`/api/documents/stats${query}`, fetcher, { refreshInterval: 60000 });
}

export function useCategories(release) {
  const query = release ? `?release=${release}` : "";
  return useSWR(`/api/documents/categories${query}`, fetcher);
}

export function useChangeFeed(params = {}) {
  const query = new URLSearchParams(params).toString();
  return useSWR(`/api/changes/feed?${query}`, fetcher, { refreshInterval: 30000 });
}

export function useDiscourse(docId, params = {}) {
  const query = new URLSearchParams(params).toString();
  return useSWR(
    docId ? `/api/discourse/${encodeURIComponent(docId)}?${query}` : null,
    fetcher
  );
}

export function useTrending(params = {}) {
  const query = new URLSearchParams(params).toString();
  return useSWR(`/api/discourse/trending?${query}`, fetcher, { refreshInterval: 60000 });
}

export function useGlossary(params = {}) {
  const query = new URLSearchParams(params).toString();
  return useSWR(`/api/glossary?${query}`, fetcher);
}

export function useHealth() {
  return useSWR("/api/health", fetcher, { refreshInterval: 30000 });
}

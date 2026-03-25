/**
 * API client for OpenDocket backend.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAPI(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  if (!res.ok) {
    const error = new Error(`API error: ${res.status}`);
    error.status = res.status;
    throw error;
  }
  return res.json();
}

// ─── Documents ─────────────────────────────────────────────────────

export function getDocuments(params = {}) {
  const query = new URLSearchParams(params).toString();
  return fetchAPI(`/api/documents?${query}`);
}

export function getDocument(id) {
  return fetchAPI(`/api/documents/${encodeURIComponent(id)}`);
}

export function getDocumentStats(release) {
  const query = release ? `?release=${release}` : "";
  return fetchAPI(`/api/documents/stats${query}`);
}

export function getCategories(release) {
  const query = release ? `?release=${release}` : "";
  return fetchAPI(`/api/documents/categories${query}`);
}

// ─── Changes ───────────────────────────────────────────────────────

export function getChangeFeed(params = {}) {
  const query = new URLSearchParams(params).toString();
  return fetchAPI(`/api/changes/feed?${query}`);
}

export function getChangeStats(release) {
  const query = release ? `?release=${release}` : "";
  return fetchAPI(`/api/changes/stats${query}`);
}

// ─── Discourse ─────────────────────────────────────────────────────

export function getDocumentDiscourse(docId, params = {}) {
  const query = new URLSearchParams(params).toString();
  return fetchAPI(`/api/discourse/${encodeURIComponent(docId)}?${query}`);
}

export function getTrending(params = {}) {
  const query = new URLSearchParams(params).toString();
  return fetchAPI(`/api/discourse/trending?${query}`);
}

export function getCoMentions(params = {}) {
  const query = new URLSearchParams(params).toString();
  return fetchAPI(`/api/discourse/co-mentions?${query}`);
}

// ─── Glossary ──────────────────────────────────────────────────────

export function getGlossary(params = {}) {
  const query = new URLSearchParams(params).toString();
  return fetchAPI(`/api/glossary?${query}`);
}

export function proposeTerm(data) {
  return fetchAPI("/api/glossary", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// ─── Config ────────────────────────────────────────────────────────

export function getReleases() {
  return fetchAPI("/api/config/releases");
}

export function getHealth() {
  return fetchAPI("/api/health");
}

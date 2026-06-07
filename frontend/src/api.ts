import type { Catalog, InteractionAnalysis, SingleAnalysis } from "./types";

const API_BASE = "http://127.0.0.1:8010/api";

async function readData<T>(response: Response): Promise<T> {
  const payload = await response.json();
  return payload.data as T;
}

export async function fetchCatalog(): Promise<Catalog> {
  return readData<Catalog>(await fetch(`${API_BASE}/catalog`));
}

export async function fetchRanking(body: unknown) {
  return readData(await fetch(`${API_BASE}/rank`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }));
}

export async function fetchSingleAnalysis(body: unknown): Promise<SingleAnalysis> {
  return readData<SingleAnalysis>(await fetch(`${API_BASE}/analyze/single`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }));
}

export async function fetchInteractionAnalysis(body: unknown): Promise<InteractionAnalysis> {
  return readData<InteractionAnalysis>(await fetch(`${API_BASE}/analyze/interaction`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  }));
}

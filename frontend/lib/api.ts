/** Browser API client for the Atlas FastAPI backend. */

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("atlas_token");
}

export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) localStorage.setItem("atlas_token", token);
  else localStorage.removeItem("atlas_token");
}

export async function api<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail || JSON.stringify(body);
      if (Array.isArray(detail)) {
        detail = detail.map((d: { msg?: string }) => d.msg || String(d)).join(", ");
      }
    } catch {
      /* ignore */
    }
    throw new ApiError(response.status, String(detail));
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export type User = {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
};

export type Project = {
  id: string;
  owner_id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
};

export type Dataset = {
  id: string;
  project_id: string;
  name: string;
  original_filename: string;
  row_count: number;
  column_count: number;
  file_size_bytes: number;
  created_at: string;
};

export type ExperimentSummary = {
  id: string;
  project_id: string;
  dataset_id: string;
  name: string;
  status: string;
  task_type: string;
  target_column: string;
  created_at: string;
};

export const authApi = {
  register: (body: {
    email: string;
    password: string;
    full_name?: string;
  }) =>
    api<User>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  login: async (body: { email: string; password: string }) => {
    const token = await api<{ access_token: string; token_type: string }>(
      "/api/v1/auth/login",
      { method: "POST", body: JSON.stringify(body) },
    );
    setToken(token.access_token);
    return token;
  },
  me: () => api<User>("/api/v1/auth/me"),
  logout: () => setToken(null),
};

export const projectsApi = {
  list: () => api<Project[]>("/api/v1/projects"),
  create: (body: { name: string; description?: string }) =>
    api<Project>("/api/v1/projects", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  get: (id: string) => api<Project>(`/api/v1/projects/${id}`),
  remove: (id: string) =>
    api<void>(`/api/v1/projects/${id}`, { method: "DELETE" }),
};

export const datasetsApi = {
  list: (projectId: string) =>
    api<Dataset[]>(`/api/v1/projects/${projectId}/datasets`),
  upload: async (projectId: string, file: File, name?: string) => {
    const form = new FormData();
    form.append("file", file);
    if (name) form.append("name", name);
    return api<Dataset>(`/api/v1/projects/${projectId}/datasets`, {
      method: "POST",
      body: form,
    });
  },
};

export const experimentsApi = {
  list: (projectId: string) =>
    api<ExperimentSummary[]>(`/api/v1/projects/${projectId}/experiments`),
};

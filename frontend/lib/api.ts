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
        detail = detail
          .map((d: { msg?: string }) => d.msg || String(d))
          .join(", ");
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

export type ColumnSchemaItem = { name: string; dtype: string };

export type Dataset = {
  id: string;
  project_id: string;
  name: string;
  original_filename: string;
  content_type?: string;
  row_count: number;
  column_count: number;
  file_size_bytes: number;
  column_schema: ColumnSchemaItem[];
  created_at: string;
  updated_at?: string;
};

export type DatasetProfile = {
  id: string;
  dataset_id: string;
  target_column: string | null;
  report: {
    summary?: {
      row_count: number;
      column_count: number;
      duplicate_row_count: number;
      duplicate_row_pct: number;
      memory_bytes_approx?: number;
    };
    columns?: Array<{
      name: string;
      dtype: string;
      inferred_type: string;
      missing_count: number;
      missing_pct: number;
      unique_count: number;
      stats?: Record<string, number | null>;
      top_values?: Array<{ value: string; count: number }>;
    }>;
    correlations?: {
      method: string;
      threshold_abs: number;
      pairs: Array<{
        column_a: string;
        column_b: string;
        coefficient: number;
        abs_coefficient: number;
        note: string;
      }>;
    };
    target_analysis?: {
      column: string;
      class_counts: Array<{ value: string; count: number }>;
      n_classes: number;
      imbalance_ratio: number | null;
      warning: string | null;
    } | null;
    warnings?: Array<{
      code: string;
      column: string;
      severity: string;
      message: string;
    }>;
  };
  created_at: string;
  updated_at: string;
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
  updated_at?: string;
};

export type Experiment = ExperimentSummary & {
  config: Record<string, unknown>;
  results: {
    data?: Record<string, unknown>;
    models?: Array<{
      model_key: string;
      model_name: string;
      metrics: Record<string, number | null>;
      train_time_seconds: number;
      notes?: string[];
    }>;
    comparison?: {
      primary_metric?: string | null;
      ranking?: Array<{ model_key: string; model_name: string; score: number }>;
      winner?: {
        model_key: string;
        model_name: string;
        score: number;
        reason: string;
      } | null;
      tradeoffs?: string[];
    };
  } | null;
  error_message: string | null;
};

export type ExperimentCreate = {
  dataset_id: string;
  name: string;
  target_column: string;
  task_type?: "classification" | "regression";
  test_size?: number;
  random_state?: number;
  models?: string[] | null;
};

export type ModelComparisonCard = {
  rank: number;
  model_key: string;
  model_name: string;
  metrics: Record<string, number | null>;
  primary_score: number | null;
  delta_vs_winner: number | null;
  train_time_seconds: number;
  is_winner: boolean;
  pros: string[];
  cons: string[];
};

export type ExperimentComparison = {
  experiment_id: string;
  experiment_name: string;
  task_type: string;
  target_column: string;
  status: string;
  primary_metric: string | null;
  winner: {
    model_key: string;
    model_name: string;
    score: number;
    reason: string;
  } | null;
  tradeoffs: string[];
  models: ModelComparisonCard[];
  metric_table: Array<Record<string, unknown>>;
};

export type Explanation = {
  id: string;
  experiment_id: string;
  model_key: string;
  report: {
    method?: string;
    summary?: string;
    feature_importances?: Array<{
      feature: string;
      mean_abs_shap: number;
      rank: number;
    }>;
    top_features?: Array<{ feature: string; mean_abs_shap: number }>;
    instance?: {
      index: number;
      top_contributions: Array<{ feature: string; shap_value: number }>;
      note?: string;
    } | null;
  };
  created_at: string;
  updated_at: string;
};

export type Deployment = {
  id: string;
  project_id: string;
  experiment_id: string;
  name: string;
  model_key: string;
  status: string;
  metadata_json: {
    feature_columns?: string[];
    model_name?: string;
  };
  prediction_count: number;
  predict_path: string | null;
  bundle_hint: string | null;
  created_at: string;
};

export type PredictResponse = {
  deployment_id: string;
  model_key: string;
  predictions: unknown[];
  probabilities: number[][] | null;
  feature_columns: string[];
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
  get: (projectId: string, datasetId: string) =>
    api<Dataset>(`/api/v1/projects/${projectId}/datasets/${datasetId}`),
  upload: async (projectId: string, file: File, name?: string) => {
    const form = new FormData();
    form.append("file", file);
    if (name) form.append("name", name);
    return api<Dataset>(`/api/v1/projects/${projectId}/datasets`, {
      method: "POST",
      body: form,
    });
  },
  profile: (projectId: string, datasetId: string, target_column?: string) =>
    api<DatasetProfile>(
      `/api/v1/projects/${projectId}/datasets/${datasetId}/profile`,
      {
        method: "POST",
        body: JSON.stringify({ target_column: target_column || null }),
      },
    ),
  getProfile: (projectId: string, datasetId: string) =>
    api<DatasetProfile>(
      `/api/v1/projects/${projectId}/datasets/${datasetId}/profile`,
    ),
};

export const experimentsApi = {
  list: (projectId: string) =>
    api<ExperimentSummary[]>(`/api/v1/projects/${projectId}/experiments`),
  get: (projectId: string, experimentId: string) =>
    api<Experiment>(
      `/api/v1/projects/${projectId}/experiments/${experimentId}`,
    ),
  create: (projectId: string, body: ExperimentCreate) =>
    api<Experiment>(`/api/v1/projects/${projectId}/experiments`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  comparison: (projectId: string, experimentId: string) =>
    api<ExperimentComparison>(
      `/api/v1/projects/${projectId}/experiments/${experimentId}/comparison`,
    ),
  explain: (
    projectId: string,
    experimentId: string,
    body: { model_key: string; max_samples?: number; instance_index?: number },
  ) =>
    api<Explanation>(
      `/api/v1/projects/${projectId}/experiments/${experimentId}/explain`,
      { method: "POST", body: JSON.stringify(body) },
    ),
  getExplanation: (
    projectId: string,
    experimentId: string,
    modelKey: string,
  ) =>
    api<Explanation>(
      `/api/v1/projects/${projectId}/experiments/${experimentId}/explanations/${modelKey}`,
    ),
};

export const deploymentsApi = {
  create: (
    projectId: string,
    body: { experiment_id: string; name: string; model_key?: string | null },
  ) =>
    api<Deployment>(`/api/v1/projects/${projectId}/deployments`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
  predict: (
    projectId: string,
    deploymentId: string,
    instances: Array<Record<string, unknown>>,
  ) =>
    api<PredictResponse>(
      `/api/v1/projects/${projectId}/deployments/${deploymentId}/predict`,
      { method: "POST", body: JSON.stringify({ instances }) },
    ),
};

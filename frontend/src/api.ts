export type Task = {
  id: string;
  title: string;
  description: string;
  difficulty: string;
  tags: string[];
  version: string;
  environment: string;
  editable: string[];
  limits: { seconds: number; memory_mb: number };
};
export type Evaluation = {
  success: boolean;
  public: { passed: number; total: number };
  hidden: { passed: number; total: number };
  regression: { passed: number; total: number };
};
export type Attempt = {
  id: string;
  task_id: string;
  task_version: string;
  strategy: string;
  status: string;
  mode: string;
  model: string;
  tokens: number | null;
  cost: number | null;
  tool_calls: number;
  diff: string;
  evaluation: Evaluation | null;
  stop_reason?: string;
  events: { id: number; kind: string; summary: string; time: number }[];
  duration?: number;
};
export type Run = {
  id: string;
  title: string;
  mode: string;
  created: number;
  attempts: Attempt[];
  cancelled: boolean;
  configuration: unknown;
  metrics: {
    valid: number;
    successes: number;
    success_rate: number | null;
    total_tokens: number | null;
    total_cost: number | null;
    cost_per_success: number | null;
    median_duration: number | null;
    infrastructure_failures: number;
  };
};
export type Health = {
  database: boolean;
  redis: boolean;
  docker_cli: boolean;
  worker_ready: boolean;
  live_configured: boolean;
};
export async function api<T>(
  path: string,
  body?: unknown,
  idempotencyKey?: string,
): Promise<T> {
  const response = await fetch(
    "/api" + path,
    body
      ? {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {}),
          },
          body: JSON.stringify(body),
        }
      : undefined,
  );
  if (!response.ok) {
    const text = await response.text();
    let detail = text;
    try {
      detail = JSON.parse(text).detail;
    } catch {
      /* plain error */
    }
    throw new Error(
      typeof detail === "string"
        ? detail
        : "Invalid settings. Check required fields and budget ranges.",
    );
  }
  return response.json();
}

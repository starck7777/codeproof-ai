import React, { useEffect, useState, useRef, useCallback } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  ArrowRight,
  ArrowUpRight,
  BarChart3,
  Box,
  CheckCircle2,
  ChevronRight,
  Clock,
  Code2,
  Download,
  FileText,
  FlaskConical,
  Gauge,
  GitBranch,
  Layers,
  Play,
  Plus,
  Radio,
  Search,
  Settings,
  ShieldCheck,
  Terminal,
  Wallet,
  XCircle,
} from "lucide-react";
import {
  ScatterChart,
  Scatter,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { api, type Task, type Run, type Attempt, type Health } from "./api";
import "./style.css";
const strategies = ["DirectPatch", "IterativeFix", "PlanVerify"];
const nav = [
  ["Overview", Gauge],
  ["Tasks", Layers],
  ["Agents", Code2],
  ["New Benchmark", Plus],
  ["Runs", Activity],
  ["Compare", BarChart3],
  ["Reports", FileText],
  ["Settings", Settings],
] as const;
const display = (n: number | null | undefined, suffix = "") =>
  n == null
    ? "Unavailable"
    : `${Number.isInteger(n) ? n : n.toFixed(2)}${suffix}`;
function App() {
  const [page, setPage] = useState(
    decodeURIComponent(location.hash.slice(1)) || "Overview",
  );
  const [tasks, setTasks] = useState<Task[]>([]);
  const [runs, setRuns] = useState<Run[]>([]);
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<Run | null>(null);
  const [attempt, setAttempt] = useState<Attempt | null>(null);
  const [query, setQuery] = useState("");
  const [difficulty, setDifficulty] = useState("all");
  const [taskIds, setTaskIds] = useState(["inclusive-range"]);
  const [agents, setAgents] = useState(["DirectPatch", "IterativeFix"]);
  const [title, setTitle] = useState("Maintenance benchmark");
  const [mode, setMode] = useState("demo");
  const [tokens, setTokens] = useState(8000);
  const [tools, setTools] = useState(12);
  const [seconds, setSeconds] = useState(120);
  const [repetitions, setRepetitions] = useState(1);
  const [model, setModel] = useState("openai/gpt-4o-mini");
  const [comparisonMode, setComparisonMode] = useState("strategies");
  const [otherModel, setOtherModel] = useState("anthropic/claude-sonnet-4-5");
  const [maxCost, setMaxCost] = useState("");
  const [workerConcurrency, setWorkerConcurrency] = useState(1);
  type SavedAgent = {
    id: string;
    name: string;
    strategy: string;
    model: string;
    version: number;
  };
  const [savedAgents, setSavedAgents] = useState<SavedAgent[]>([]);
  const [agentName, setAgentName] = useState("My agent");
  const [agentStrategy, setAgentStrategy] = useState("DirectPatch");
  const [editingAgent, setEditingAgent] = useState<string | null>(null);
  const pendingStart = useRef(crypto.randomUUID());
  const [busy, setBusy] = useState(false);
  const [connection, setConnection] = useState("");
  const selectedId = selected?.id;
  const navigate = (name: string) => {
    setPage(name);
    location.hash = name;
    setError("");
    setAttempt(null);
  };
  const load = useCallback(async () => {
    try {
      const [t, r, h, saved, settings] = await Promise.all([
        api<Task[]>("/tasks"),
        api<Run[]>("/runs"),
        api<Health>("/health"),
        api<SavedAgent[]>("/agents"),
        api<{ worker_concurrency: number }>("/settings"),
      ]);
      setWorkerConcurrency(settings.worker_concurrency);
      setSavedAgents(saved);
      setTasks(t);
      setRuns(r);
      setHealth(h);
      setError("");
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    void load();
    const onHash = () =>
      setPage(decodeURIComponent(location.hash.slice(1)) || "Overview");
    const reconnect = () => {
      void load();
      const id = localStorage.getItem("codeproof-run");
      if (decodeURIComponent(location.hash.slice(1)) === "Run Detail" && id) {
        api<Run>("/runs/" + id)
          .then(setSelected)
          .catch((e) => setError(String(e)));
      }
    };
    window.addEventListener("online", reconnect);
    window.addEventListener("hashchange", onHash);
    return () => {
      window.removeEventListener("hashchange", onHash);
      window.removeEventListener("online", reconnect);
    };
  }, [load]);
  useEffect(() => {
    if (page !== "Run Detail" || !selectedId) return;
    const id = selectedId;
    localStorage.setItem("codeproof-run", id);
    const source = new EventSource(`/api/runs/${id}/events`);
    source.addEventListener("snapshot", (event) => {
      const value = JSON.parse((event as MessageEvent).data) as Run;
      setSelected(value);
      setRuns((prev) => [value, ...prev.filter((r) => r.id !== id)]);
      setConnection("Connected");
    });
    source.onerror = () => setConnection("Reconnecting…");
    source.onopen = () => setConnection("Connected");
    return () => source.close();
  }, [page, selectedId]);
  useEffect(() => {
    if (page === "Run Detail" && !selected) {
      const id = localStorage.getItem("codeproof-run");
      if (id)
        api<Run>("/runs/" + id)
          .then(setSelected)
          .catch((e) => setError(String(e)));
    }
  }, [page, selected]);
  const openRun = (run: Run) => {
    setSelected(run);
    navigate("Run Detail");
  };
  const toggle = (list: string[], value: string, set: (v: string[]) => void) =>
    set(
      list.includes(value) ? list.filter((v) => v !== value) : [...list, value],
    );
  async function start() {
    setBusy(true);
    setError("");
    try {
      const run = await api<Run>(
        "/runs",
        {
          title,
          mode,
          task_ids: taskIds,
          strategies: comparisonMode === "models" ? agents.slice(0, 1) : agents,
          comparison_mode: comparisonMode,
          models: comparisonMode === "models" ? [model, otherModel] : [],
          model,
          repetitions,
          budget: {
            tokens,
            tool_calls: tools,
            seconds,
            max_cost: maxCost === "" ? null : Number(maxCost),
          },
        },
        pendingStart.current,
      );
      pendingStart.current = crypto.randomUUID();
      openRun(run);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }
  const demo = runs.filter((r) => r.mode === "demo");
  const valid = demo.reduce((n, r) => n + r.metrics.valid, 0);
  const wins = demo.reduce((n, r) => n + r.metrics.successes, 0);
  const chart = strategies.map((strategy) => {
    const a = demo
      .flatMap((r) => r.attempts)
      .filter((a) => a.strategy === strategy && a.evaluation);
    return {
      name: strategy,
      success: a.length
        ? (100 * a.filter((a) => a.evaluation?.success).length) / a.length
        : 0,
      samples: a.length,
    };
  });
  const badge = (status: string) => (
    <span className={`badge ${status.toLowerCase().replaceAll(" ", "-")}`}>
      {status}
    </span>
  );
  const runList = (list: Run[]) => (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>BENCHMARK</th>
            <th>MODE</th>
            <th>ATTEMPTS</th>
            <th>STRICT SUCCESS</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {list.map((r) => (
            <tr key={r.id}>
              <td>
                <button className="text-button" onClick={() => openRun(r)}>
                  {r.title}
                </button>
                <small>{new Date(r.created * 1000).toLocaleString()}</small>
              </td>
              <td>{badge(r.mode === "demo" ? "Demo Replay" : "Live")}</td>
              <td>
                {
                  r.attempts.filter((a) =>
                    ["Completed", "Failed", "Cancelled", "Timed Out"].includes(
                      a.status,
                    ),
                  ).length
                }{" "}
                / {r.attempts.length}
              </td>
              <td>
                {r.metrics.successes} / {r.metrics.valid}
                <small>
                  {r.metrics.infrastructure_failures} infrastructure failures
                </small>
              </td>
              <td>
                <button
                  aria-label={"Open " + r.title}
                  className="icon-button"
                  onClick={() => openRun(r)}
                >
                  <ArrowUpRight size={18} />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {!list.length && (
        <div className="empty">
          <FlaskConical size={28} />
          <h3>Your first benchmark starts here</h3>
          <p>
            Choose tasks and agent strategies to build a reproducible
            comparison.
          </p>
          <button
            className="secondary"
            onClick={() => navigate("New Benchmark")}
          >
            Configure benchmark <ArrowRight size={15} />
          </button>
        </div>
      )}
    </div>
  );
  return (
    <div className="app">
      <aside>
        <a
          href="#Overview"
          className="brand"
          onClick={() => navigate("Overview")}
        >
          <div className="brand-icon">
            <Code2 size={23} />
          </div>
          <span>
            CodeProof<span className="ai">AI</span>
            <small>AGENT EVALUATION PLATFORM</small>
          </span>
        </a>
        <div className="workspace">
          <div className="workspace-mark">C</div>
          <div>
            Local workspace<small>Hackathon edition</small>
          </div>
          <ChevronRight size={15} />
        </div>
        <p className="nav-label">WORKSPACE</p>
        <nav>
          {nav.map(([name, Icon]) => (
            <button
              key={name}
              className={page === name ? "active" : ""}
              onClick={() => navigate(name)}
            >
              <Icon size={18} />
              {name}
              {name === "New Benchmark" && <span className="shortcut">N</span>}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="integrity">
            <ShieldCheck size={20} />
            <strong>Evidence over answers</strong>
            <p>
              Isolated workspaces.
              <br />
              Trusted evaluations.
              <br />
              Transparent results.
            </p>
          </div>
          <div className="local">
            <i />
            Local environment<span>v0.1</span>
          </div>
        </div>
      </aside>
      <div className="shell">
        <header>
          <span>
            Workspace <ChevronRight size={13} /> <strong>{page}</strong>
          </span>
          <div>
            <span className="local-chip">
              <i /> LOCAL ONLY
            </span>
            <a
              href="http://127.0.0.1:8000/docs"
              target="_blank"
              rel="noreferrer"
            >
              API docs <ArrowUpRight size={13} />
            </a>
            <div className="avatar">CP</div>
          </div>
        </header>
        <main>
          <div className="page-title">
            <div>
              <p className="eyebrow">BENCHMARKING, WITH PROOF</p>
              <h1>
                {page === "Overview"
                  ? "Agent performance. Verified."
                  : page === "Run Detail"
                    ? selected?.title || "Benchmark evidence"
                    : page}
              </h1>
              <p>
                {page === "Overview"
                  ? "Measure how agents work, not just what models say."
                  : "Reproducible tasks. Equal budgets. Inspectable evidence."}
              </p>
            </div>
            {page !== "New Benchmark" && (
              <button
                className="primary"
                onClick={() => navigate("New Benchmark")}
              >
                <Plus size={17} /> New benchmark
              </button>
            )}
          </div>
          <div className="demo-banner">
            <div>
              <Radio size={18} />
              <strong>
                {(page === "Run Detail"
                  ? selected?.mode
                  : page === "New Benchmark"
                    ? mode
                    : "demo") === "live"
                  ? "Live Benchmark"
                  : "Demo Replay"}
              </strong>
              <span>
                {(page === "Run Detail"
                  ? selected?.mode
                  : page === "New Benchmark"
                    ? mode
                    : "demo") === "live"
                  ? "Actual gateway calls and isolated execution."
                  : "Deterministic agent actions — not live model results."}
              </span>
            </div>
            <button onClick={() => navigate("Settings")}>
              Environment details <ArrowRight size={14} />
            </button>
          </div>
          {error && (
            <div className="error" role="alert">
              <XCircle size={18} />
              {error}
              <button onClick={() => void load()}>Retry</button>
            </div>
          )}
          {loading ? (
            <div className="empty" role="status">
              Loading workspace…
            </div>
          ) : (
            <>
              {page === "Overview" && (
                <>
                  <div className="stats">
                    {[
                      [
                        CheckCircle2,
                        "Strict task success",
                        valid ? `${Math.round((wins / valid) * 100)}%` : "—",
                        `${wins} successful / ${valid} valid attempts`,
                      ],
                      [
                        Activity,
                        "Benchmark runs",
                        String(runs.length),
                        "Demo and live remain separate",
                      ],
                      [
                        Terminal,
                        "Model tokens",
                        "Unavailable",
                        "Demo does not consume model tokens",
                      ],
                      [
                        Wallet,
                        "Inference cost",
                        "Unavailable",
                        "No configured pricing snapshot",
                      ],
                    ].map(([Icon, label, value, caption]) => {
                      const I = Icon as typeof Activity;
                      return (
                        <section className="stat" key={String(label)}>
                          <div>
                            <span>{String(label)}</span>
                            <I size={17} />
                          </div>
                          <strong>{String(value)}</strong>
                          <small>{String(caption)}</small>
                        </section>
                      );
                    })}
                  </div>
                  <div className="overview-grid">
                    <section className="card">
                      <div className="card-heading">
                        <div>
                          <h2>Strategy comparison</h2>
                          <p>Strict success rate · Demo Replay only</p>
                        </div>
                        <span className="subtle">
                          {valid} evaluated attempts
                        </span>
                      </div>
                      <div className="chart">
                        <ResponsiveContainer width="100%" height={230}>
                          <BarChart
                            data={chart}
                            margin={{ left: -20, right: 20, top: 15 }}
                          >
                            <CartesianGrid
                              strokeDasharray="3 3"
                              vertical={false}
                              stroke="#e9edf2"
                            />
                            <XAxis
                              dataKey="name"
                              tickLine={false}
                              axisLine={false}
                              fontSize={12}
                            />
                            <YAxis
                              domain={[0, 100]}
                              unit="%"
                              tickLine={false}
                              axisLine={false}
                              fontSize={11}
                            />
                            <Tooltip />
                            <Bar
                              dataKey="success"
                              fill="#159a8b"
                              radius={[5, 5, 0, 0]}
                              maxBarSize={65}
                            />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                      {!valid && (
                        <p className="chart-note">
                          No evaluated evidence yet. Rates appear after trusted
                          evaluation.
                        </p>
                      )}
                    </section>
                    <section className="card readiness">
                      <div className="card-heading">
                        <div>
                          <h2>Execution readiness</h2>
                          <p>Your local benchmark environment</p>
                        </div>
                        <ShieldCheck size={19} />
                      </div>
                      {[
                        ["Database", health?.database],
                        ["Redis queue", health?.redis],
                        ["Trusted worker", health?.worker_ready],
                        ["Live gateway configured", health?.live_configured],
                      ].map(([label, ok]) => (
                        <div className="readiness-line" key={String(label)}>
                          <span>
                            <i className={ok ? "ok" : ""} />
                            {String(label)}
                          </span>
                          <b>{ok ? "Available" : "Unavailable"}</b>
                        </div>
                      ))}
                      <p className="note">
                        Live readiness requires a running Docker engine, task
                        image and worker. No host execution fallback.
                      </p>
                      <button
                        className="text-button"
                        onClick={() => navigate("Settings")}
                      >
                        View setup requirements <ArrowRight size={14} />
                      </button>
                    </section>
                  </div>
                  <section className="card recent">
                    <div className="card-heading">
                      <div>
                        <h2>Recent benchmarks</h2>
                        <p>Every result has a trace, a patch, and a verdict.</p>
                      </div>
                      <button
                        className="text-button"
                        onClick={() => navigate("Runs")}
                      >
                        View all runs <ArrowRight size={14} />
                      </button>
                    </div>
                    {runList(runs.slice(0, 5))}
                  </section>
                  <div className="bottom-note">
                    <ShieldCheck size={16} />
                    <span>Benchmark integrity by design</span>
                    <p>
                      Hidden tests stay outside agent workspaces. Only permitted
                      source changes reach evaluation.
                    </p>
                    <a
                      href="http://127.0.0.1:8000/docs"
                      target="_blank"
                      rel="noreferrer"
                    >
                      Explore the API <ArrowUpRight size={14} />
                    </a>
                  </div>
                </>
              )}
              {page === "Tasks" && (
                <>
                  <div className="filters">
                    <label className="search">
                      <Search size={17} />
                      <input
                        aria-label="Search tasks or tags"
                        placeholder="Search tasks or tags"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                      />
                    </label>
                    <select
                      aria-label="Difficulty"
                      value={difficulty}
                      onChange={(e) => setDifficulty(e.target.value)}
                    >
                      <option value="all">All difficulties</option>
                      {["easy", "medium", "hard"].map((v) => (
                        <option key={v}>{v}</option>
                      ))}
                    </select>
                    <span>{tasks.length} original Python tasks</span>
                  </div>
                  <div className="task-grid">
                    {tasks
                      .filter(
                        (t) =>
                          (difficulty === "all" ||
                            t.difficulty === difficulty) &&
                          (t.title + " " + t.tags.join(" "))
                            .toLowerCase()
                            .includes(query.toLowerCase()),
                      )
                      .map((t) => (
                        <article className="card task" key={t.id}>
                          <div>
                            <span className={"badge " + t.difficulty}>
                              {t.difficulty}
                            </span>
                            <small>v{t.version}</small>
                          </div>
                          <h2>{t.title}</h2>
                          <p>{t.description}</p>
                          <div className="tags">
                            {t.tags.map((tag) => (
                              <span key={tag}>{tag}</span>
                            ))}
                          </div>
                          <details>
                            <summary>Environment & protected files</summary>
                            <p>
                              {t.environment} · {t.limits.memory_mb} MB ·{" "}
                              {t.limits.seconds}s per test phase. Editable:{" "}
                              {t.editable.join(", ")}. Public tests: 1; hidden:
                              2; regression: 1. All other paths are protected.
                            </p>
                          </details>
                          <button
                            className="text-button"
                            onClick={() => {
                              setTaskIds([t.id]);
                              navigate("New Benchmark");
                            }}
                          >
                            Benchmark task <ArrowRight size={14} />
                          </button>
                        </article>
                      ))}
                  </div>
                </>
              )}
              {page === "New Benchmark" && (
                <div className="form-layout">
                  <section className="card form">
                    <h2>Configure your benchmark</h2>
                    <label>
                      Run title
                      <input
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        maxLength={100}
                      />
                    </label>
                    <label>
                      Execution mode
                      <select
                        value={mode}
                        onChange={(e) => setMode(e.target.value)}
                      >
                        <option value="demo">
                          Demo Replay — deterministic actions
                        </option>
                        <option value="live">
                          Live Benchmark — actual gateway calls
                        </option>
                      </select>
                    </label>
                    <label>
                      Comparison mode
                      <select
                        value={comparisonMode}
                        onChange={(e) => setComparisonMode(e.target.value)}
                      >
                        <option value="strategies">
                          Same model, different strategies
                        </option>
                        <option value="models">
                          Same strategy, different models
                        </option>
                      </select>
                    </label>
                    {comparisonMode === "models" && (
                      <p className="note">
                        The first selected strategy is used for both models.
                      </p>
                    )}
                    <fieldset>
                      <legend>1. Choose tasks</legend>
                      <div className="checkbox-grid">
                        {tasks.map((t) => (
                          <label key={t.id}>
                            <input
                              type="checkbox"
                              checked={taskIds.includes(t.id)}
                              onChange={() => toggle(taskIds, t.id, setTaskIds)}
                            />
                            <span>
                              {t.title}
                              <small>
                                {t.difficulty} · v{t.version}
                              </small>
                            </span>
                          </label>
                        ))}
                      </div>
                    </fieldset>
                    <fieldset>
                      <legend>2. Choose agent strategies</legend>
                      {strategies.map((s) => (
                        <label className="check" key={s}>
                          <input
                            type="checkbox"
                            checked={agents.includes(s)}
                            onChange={() => toggle(agents, s, setAgents)}
                          />
                          {s} Agent
                        </label>
                      ))}
                    </fieldset>
                    <label>
                      Model / provider
                      <input
                        value={model}
                        onChange={(e) => setModel(e.target.value)}
                      />
                    </label>
                    {comparisonMode === "models" && (
                      <label>
                        Second model / provider
                        <input
                          value={otherModel}
                          onChange={(e) => setOtherModel(e.target.value)}
                        />
                      </label>
                    )}
                    <label>
                      Maximum estimated cost (USD, optional)
                      <input
                        type="number"
                        min="0"
                        max="100"
                        step="0.01"
                        value={maxCost}
                        onChange={(e) => setMaxCost(e.target.value)}
                      />
                    </label>
                    <fieldset>
                      <legend>3. Equal per-attempt budgets</legend>
                      <div className="budget-grid">
                        {[
                          ["Max tokens", tokens, setTokens, 256, 64000],
                          ["Tool calls", tools, setTools, 1, 50],
                          ["Deadline (seconds)", seconds, setSeconds, 10, 600],
                          ["Repetitions", repetitions, setRepetitions, 1, 3],
                        ].map(([label, value, set, min, max]) => (
                          <label key={String(label)}>
                            {String(label)}
                            <input
                              type="number"
                              value={value as number}
                              min={min as number}
                              max={max as number}
                              onChange={(e) =>
                                (set as (n: number) => void)(
                                  Number(e.target.value),
                                )
                              }
                            />
                          </label>
                        ))}
                      </div>
                    </fieldset>
                  </section>
                  <section className="card summary">
                    <span className="eyebrow">REVIEW BEFORE STARTING</span>
                    <h2>Reproducible by default.</h2>
                    <p>
                      {taskIds.length} tasks × {agents.length} strategies ×{" "}
                      {repetitions} repetitions
                    </p>
                    <strong className="big-number">
                      {taskIds.length *
                        (comparisonMode === "models" ? 2 : agents.length) *
                        repetitions}
                      <small>total attempts</small>
                    </strong>
                    <hr />
                    <p>
                      Tokens: {tokens.toLocaleString()} / attempt
                      <br />
                      Tools: {tools} / attempt
                      <br />
                      Deadline: {seconds}s / attempt
                      <br />
                      Mode: {mode === "demo" ? "Demo Replay" : "Live Benchmark"}
                    </p>
                    <p className="note">
                      Configuration is frozen at start. Demo usage and costs are
                      unavailable. Hidden feedback never returns to the agent.
                    </p>
                    {!health?.docker_cli && !health?.worker_ready && (
                      <p className="error">
                        Docker unavailable. Install Docker to enable isolated
                        execution.
                      </p>
                    )}
                    <button
                      className="primary"
                      disabled={busy || !taskIds.length || !agents.length}
                      onClick={() => void start()}
                    >
                      <Play size={16} />
                      {busy ? "Starting…" : "Confirm & start benchmark"}
                    </button>
                  </section>
                </div>
              )}
              {(page === "Runs" || page === "Reports") && (
                <section className="card">
                  {runList(runs)}
                  {page === "Reports" &&
                    runs.map((r) => (
                      <div className="report-row" key={r.id}>
                        <strong>{r.title}</strong>
                        {["json", "csv", "html"].map((f) => (
                          <a
                            className="secondary"
                            key={f}
                            href={`/api/runs/${r.id}/report/${f}`}
                          >
                            <Download size={14} />
                            {f.toUpperCase()}
                          </a>
                        ))}
                      </div>
                    ))}
                </section>
              )}
              {page === "Run Detail" && selected && (
                <>
                  <div className="run-toolbar">
                    <span className="badge">
                      {selected.mode === "demo"
                        ? "Demo Replay — not live model results"
                        : "Live Benchmark"}
                    </span>
                    <span>{connection}</span>
                    <button
                      className="secondary"
                      onClick={async () => {
                        try {
                          setSelected(
                            await api<Run>(`/runs/${selected.id}/cancel`, {}),
                          );
                        } catch (e) {
                          setError(String(e));
                        }
                      }}
                    >
                      Cancel run
                    </button>
                    {["json", "csv", "html"].map((f) => (
                      <a
                        className="secondary"
                        key={f}
                        href={`/api/runs/${selected.id}/report/${f}`}
                      >
                        <Download size={14} />
                        {f.toUpperCase()}
                      </a>
                    ))}
                  </div>
                  <div className="attempt-grid">
                    {selected.attempts.map((a) => (
                      <button
                        className="card attempt"
                        key={a.id}
                        onClick={() => setAttempt(a)}
                      >
                        <div>
                          {badge(a.status)}
                          <ChevronRight size={16} />
                        </div>
                        <h2>{a.task_id}</h2>
                        <p>{a.strategy} Agent</p>
                        <div className="attempt-metrics">
                          <span>
                            <Terminal size={14} />
                            {a.tool_calls} tools
                          </span>
                          <span>
                            <Clock size={14} />
                            {display(a.duration, "s")}
                          </span>
                        </div>
                        <p>
                          {a.evaluation
                            ? `${a.evaluation.success ? "Strict success" : "Tests failed"} · hidden ${a.evaluation.hidden.passed}/${a.evaluation.hidden.total}`
                            : a.stop_reason || "Awaiting evaluation"}
                        </p>
                      </button>
                    ))}
                  </div>
                  {attempt && (
                    <section className="card evidence">
                      <div className="card-heading">
                        <h2>Attempt evidence · {attempt.strategy}</h2>
                        {badge(attempt.status)}
                      </div>
                      <p>{attempt.stop_reason}</p>
                      <p>
                        Tokens: {display(attempt.tokens)} · Cost:{" "}
                        {display(attempt.cost)} · Task v{attempt.task_version} ·{" "}
                        {attempt.model}
                      </p>
                      <h3>Final patch</h3>
                      <pre>{attempt.diff || "No patch available."}</pre>
                      <h3>Observable execution trace</h3>
                      {attempt.events.map((e) => (
                        <div className="event" key={e.id}>
                          <span>
                            {new Date(e.time * 1000).toLocaleTimeString()}
                          </span>
                          <strong>{e.kind}</strong>
                          <pre>{e.summary}</pre>
                        </div>
                      ))}
                    </section>
                  )}
                  <details className="card config">
                    <summary>Immutable configuration snapshot</summary>
                    <pre>{JSON.stringify(selected.configuration, null, 2)}</pre>
                  </details>
                </>
              )}
              {page === "Compare" && (
                <>
                  <p className="note">
                    Strict success is the primary comparison. Only compare
                    matching task versions, environments and budgets.
                    Repetitions are not pass@k.
                  </p>
                  {["demo", "live"].map((m) => {
                    const values = runs.filter((r) => r.mode === m);
                    const chartData = values.map((r) => ({
                      name: r.title,
                      success: (r.metrics.success_rate || 0) * 100,
                      duration: r.metrics.median_duration,
                      cost: r.metrics.total_cost,
                    }));
                    const configurations = [
                      ...new Set(
                        values.map((r) => JSON.stringify(r.configuration)),
                      ),
                    ];
                    return (
                      <section className="card recent" key={m}>
                        <div className="card-heading">
                          <h2>
                            {m === "demo" ? "Demo Replay" : "Live Benchmark"}
                          </h2>
                          <span className="subtle">{values.length} runs</span>
                        </div>
                        {configurations.length > 1 && (
                          <p className="error" style={{ margin: 20 }}>
                            Configurations differ. Inspect snapshots before
                            drawing comparisons.
                          </p>
                        )}
                        {values.length > 0 && (
                          <>
                            <div
                              className="overview-grid"
                              style={{ padding: 20 }}
                            >
                              <div>
                                <h3>Success rate (%)</h3>
                                <ResponsiveContainer width="100%" height={190}>
                                  <BarChart data={chartData}>
                                    <XAxis dataKey="name" fontSize={9} />
                                    <YAxis domain={[0, 100]} fontSize={10} />
                                    <Tooltip />
                                    <Bar dataKey="success" fill="#159a8b" />
                                  </BarChart>
                                </ResponsiveContainer>
                              </div>
                              <div>
                                <h3>Median duration (seconds)</h3>
                                <ResponsiveContainer width="100%" height={190}>
                                  <BarChart
                                    data={chartData.filter(
                                      (d) => d.duration != null,
                                    )}
                                  >
                                    <XAxis dataKey="name" fontSize={9} />
                                    <YAxis fontSize={10} />
                                    <Tooltip />
                                    <Bar dataKey="duration" fill="#627d9d" />
                                  </BarChart>
                                </ResponsiveContainer>
                              </div>
                            </div>
                            <div style={{ padding: "0 20px" }}>
                              <h3>Cost versus success</h3>
                              {chartData.some((d) => d.cost != null) ? (
                                <ResponsiveContainer width="100%" height={180}>
                                  <ScatterChart>
                                    <XAxis
                                      dataKey="cost"
                                      name="Cost (USD)"
                                      type="number"
                                    />
                                    <YAxis
                                      dataKey="success"
                                      name="Success (%)"
                                      type="number"
                                    />
                                    <Tooltip />
                                    <Scatter
                                      data={chartData.filter(
                                        (d) => d.cost != null,
                                      )}
                                      fill="#159a8b"
                                    />
                                  </ScatterChart>
                                </ResponsiveContainer>
                              ) : (
                                <p className="note">
                                  Unavailable — no measured cost data. Demo
                                  replay does not have model usage.
                                </p>
                              )}
                            </div>
                          </>
                        )}
                        {runList(values)}
                        {values.length > 0 && (
                          <div className="table-wrap">
                            <table>
                              <thead>
                                <tr>
                                  <th>TASK / VERSION</th>
                                  {values.map((r) => (
                                    <th key={r.id}>{r.title}</th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody>
                                {[
                                  ...new Set(
                                    values.flatMap((r) =>
                                      r.attempts.map(
                                        (a) => a.task_id + "@" + a.task_version,
                                      ),
                                    ),
                                  ),
                                ].map((key) => (
                                  <tr key={key}>
                                    <td>{key}</td>
                                    {values.map((r) => (
                                      <td key={r.id}>
                                        {r.attempts
                                          .filter(
                                            (a) =>
                                              a.task_id +
                                                "@" +
                                                a.task_version ===
                                              key,
                                          )
                                          .map((a) => (
                                            <button
                                              key={a.id}
                                              className="text-button"
                                              style={{
                                                display: "flex",
                                                marginBottom: 6,
                                              }}
                                              onClick={() => {
                                                openRun(r);
                                                setAttempt(a);
                                              }}
                                            >
                                              {a.strategy} ·{" "}
                                              {a.evaluation
                                                ? a.evaluation.success
                                                  ? "Passed"
                                                  : "Failed"
                                                : a.status}{" "}
                                              <ArrowUpRight size={12} />
                                            </button>
                                          ))}
                                      </td>
                                    ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </section>
                    );
                  })}
                </>
              )}
              {page === "Agents" && (
                <section className="card form" style={{ marginBottom: 20 }}>
                  <h2>Saved agent configurations</h2>
                  <div className="budget-grid">
                    <label>
                      Configuration name
                      <input
                        value={agentName}
                        onChange={(e) => setAgentName(e.target.value)}
                      />
                    </label>
                    <label>
                      Strategy
                      <select
                        value={agentStrategy}
                        onChange={(e) => setAgentStrategy(e.target.value)}
                      >
                        {strategies.map((s) => (
                          <option key={s}>{s}</option>
                        ))}
                      </select>
                    </label>
                    <label>
                      Provider / model
                      <input
                        value={model}
                        onChange={(e) => setModel(e.target.value)}
                      />
                    </label>
                  </div>
                  <button
                    className="primary"
                    onClick={async () => {
                      try {
                        await api(
                          "/agents" + (editingAgent ? "/" + editingAgent : ""),
                          { name: agentName, strategy: agentStrategy, model },
                        );
                        setEditingAgent(null);
                        await load();
                      } catch (e) {
                        setError(String(e));
                      }
                    }}
                  >
                    {editingAgent ? "Save new version" : "Save configuration"}
                  </button>
                  {savedAgents.map((a) => (
                    <div className="report-row" key={a.id}>
                      <strong>
                        {a.name}
                        <small>
                          v{a.version} · {a.strategy} · {a.model}
                        </small>
                      </strong>
                      <button
                        className="secondary"
                        onClick={() => {
                          setEditingAgent(a.id);
                          setAgentName(a.name);
                          setAgentStrategy(a.strategy);
                          setModel(a.model);
                        }}
                      >
                        Edit
                      </button>
                      <button
                        className="secondary"
                        onClick={async () => {
                          try {
                            await api("/agents", {
                              name: a.name + " copy",
                              strategy: a.strategy,
                              model: a.model,
                            });
                            await load();
                          } catch (e) {
                            setError(String(e));
                          }
                        }}
                      >
                        Duplicate
                      </button>
                      <button
                        className="secondary"
                        onClick={() => {
                          setAgents([a.strategy]);
                          setModel(a.model);
                          navigate("New Benchmark");
                        }}
                      >
                        Use
                      </button>
                    </div>
                  ))}
                </section>
              )}
              {page === "Agents" && (
                <div className="task-grid">
                  {strategies.map((s, i) => (
                    <section className="card task" key={s}>
                      <div className="agent-icon">
                        <GitBranch size={22} />
                      </div>
                      <h2>{s} Agent</h2>
                      <p>
                        {
                          [
                            "Inspect source, apply a focused patch, then verify with at most one public test call.",
                            "Inspect and test first, then repeatedly edit and test based on public feedback.",
                            "Start with a brief operational plan; inspect, fix, and verify before finishing.",
                          ][i]
                        }
                      </p>
                      <p className="note">
                        Demo:{" "}
                        {
                          [
                            "scripted reference fix",
                            "intentional failed patch (starter retained)",
                            "planned reference fix",
                          ][i]
                        }
                        . All results require trusted evaluation.
                      </p>
                      <button
                        className="secondary"
                        onClick={() => {
                          setAgents([s]);
                          navigate("New Benchmark");
                        }}
                      >
                        Use strategy <ArrowRight size={14} />
                      </button>
                    </section>
                  ))}
                </div>
              )}
              {page === "Settings" && (
                <section className="card settings">
                  <h2>Local integration settings</h2>
                  <p>
                    Credentials and gateway origins are configured on the
                    server. They are never sent to this interface or execution
                    containers.
                  </p>
                  <div className="code-block">
                    <pre>
                      make setup{"\n"}make up{"\n"}make worker
                    </pre>
                  </div>
                  <h3>Environment readiness</h3>
                  {health &&
                    Object.entries(health).map(([k, v]) => (
                      <p key={k}>
                        <span className="badge">
                          {v ? "Available" : "Unavailable"}
                        </span>{" "}
                        {k.replaceAll("_", " ")}
                      </p>
                    ))}
                  <h3>Worker concurrency</h3>
                  <p>
                    Applies to the full-stack launcher. Existing jobs finish
                    before a worker shuts down.
                  </p>
                  <label>
                    Concurrent workers
                    <input
                      aria-label="Concurrent workers"
                      type="number"
                      min="1"
                      max="4"
                      value={workerConcurrency}
                      onChange={(e) =>
                        setWorkerConcurrency(Number(e.target.value))
                      }
                    />
                  </label>
                  <button
                    className="secondary"
                    onClick={async () => {
                      try {
                        await api("/settings", {
                          worker_concurrency: workerConcurrency,
                        });
                        setError("");
                      } catch (e) {
                        setError(String(e));
                      }
                    }}
                  >
                    Save worker settings
                  </button>
                  <h3>Bifrost</h3>
                  <p>
                    Configure BIFROST_URL, GATEWAY_ALLOWED_ORIGINS and
                    BIFROST_VIRTUAL_KEY in the trusted worker environment. Live
                    integration has not been verified on this host.
                  </p>
                  <p className="note">
                    No authentication is provided in this local MVP. Keep every
                    service bound to localhost. Public hosting requires
                    authentication, ownership checks and a stronger execution
                    boundary.
                  </p>
                  <button className="secondary" onClick={() => void load()}>
                    Refresh readiness
                  </button>
                </section>
              )}
            </>
          )}
          <footer>
            <span>CodeProof AI</span>
            <span>
              <Box size={13} /> Python task suite v1.0 · Evidence-based
              evaluation
            </span>
            <span>Built for workflows, not just responses.</span>
          </footer>
        </main>
      </div>
    </div>
  );
}
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

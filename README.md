# CodeProof AI

Evidence-based benchmarking for coding and bug-fixing **agents**, including their edits, test calls, budgets and stopping behavior. Built for researchers and teams comparing maintenance workflows.

**Status:** local MVP under verification. See `FINAL_TEST_REPORT.md` for actual checks and `IMPLEMENTATION_CHECKLIST.md` for remaining work. Demo Replay is deterministic scripted behavior, never model-performance evidence. No cloud deployment is included.

## Quick start

Requires Python 3.12+, Node 22+, Docker Desktop/Engine and Compose. Use an otherwise free localhost port 8000, 5173, 5432 and 6379. Do not stop unrelated processes; configure alternate ports consistently if occupied.

```sh
make setup
make start
```

Open http://127.0.0.1:5173 after `/api/health` reports the database and Redis available. The task image must be built and the host worker running. API documentation: http://127.0.0.1:8000/docs. API never imports the execution runner.

The trusted worker runs on the Docker host so its temporary bind paths are meaningful to the Docker engine. Compose starts PostgreSQL, Redis, migration and API services; the worker is deliberately outside task containers and holds Docker privileges. Database/Redis ports are loopback-only because the host worker needs them. Never expose these services publicly.

Stop the full stack with `make stop-all` (or Ctrl-C in the launcher). It stops only owned processes and Compose services, without deleting volumes. To run services separately use `make up`, `make worker`, and `npm run dev --prefix frontend`. For read-only exploration without Docker: `make dev`; stop with `make stop`. This starts a separate SQLite development database, API and frontend. It cannot execute code without Docker/Redis. Never run `make dev` alongside Compose API on port 8000.

## Workflow

1. Tasks: search 12 original versioned Python fixtures, inspect requirements and editable-file rules.
2. New Benchmark: select tasks, strategies, repetitions and equal token/tool/time budgets.
3. Confirm the frozen configuration. Demo mode scripts reference fixes for DirectPatch/PlanVerify and an intentional failure for IterativeFix. Lower tool budgets demonstrate exhaustion.
4. Inspect SSE snapshots, tool actions, final source diff and separate trusted test counts.
5. Compare demo and live groups separately; export JSON, CSV or printable HTML from the run.

No seeded success statistics are invented. Without Docker, task/strategy exploration works and starting execution gives a clear unavailable response.

## Live Bifrost

Official references consulted during implementation:
- https://docs.getbifrost.ai/quickstart/gateway/setting-up
- https://docs.getbifrost.ai/quickstart/gateway/provider-configuration
- https://docs.getbifrost.ai/features/governance/virtual-keys

Install/configure Bifrost using its official instructions, bind it locally, and configure provider credentials in Bifrost. The worker calls `/v1/chat/completions` using a `provider/model` identifier and optional `x-bf-vk` virtual-key header. Gateways with inference auth enabled also require `BIFROST_AUTHORIZATION` (Basic header value). Use a private `.env` file and export its values in the worker shell; files are not loaded implicitly. Do not put keys in Vite variables. Both `BIFROST_URL` and `GATEWAY_ALLOWED_ORIGINS` must contain the same exact origin. Redirects and environment proxies are disabled. The UI cannot change gateway URLs.

Restart the API with `BIFROST_URL` configured to enable its live readiness flag. Compose passes only selected environment fields; see its API environment mapping. A configured flag does not prove connectivity. Live requests are non-streaming and use JSON controlled actions rather than native model tool calling. Transient 429/502/503 responses retry at most once. Usage absence aborts rather than inventing counts. A model change invalidates the attempt; cross-provider fallback must be disabled at Bifrost for fair comparisons. Only run live after setting your own bounded spending limit and pricing configuration.

`PRICING_FILE` maps exact model identifiers to objects with `currency: "USD"`, `date: "YYYY-MM-DD"`, `source`, `assumptions`, `input_per_million`, and `output_per_million`. Values are snapshotted per attempt. No built-in prices are presented as current. API budgets optionally accept `max_cost`; missing pricing rejects a cost-limited run. Usage is retained per request. Estimates exclude unreported retry billing and special caching/discount rules; document these in assumptions.

## Verification

```sh
make verify
```

Runs formatting/lint, TypeScript, backend tests, disposable migration persistence tests, production build, browser exploration, real Docker fixture/evaluator checks, scans, exports and separation checks. Any required failure or missing Docker returns nonzero. Actual output is summarized in `FINAL_TEST_REPORT.md`; full logs are ignored under `.local/verification`. No existing user database is reset. Browser test data must use a disposable database and separate Redis DB. No paid requests occur by default.

`make test` is faster and may skip Docker checks when Docker is unavailable. A skipped Docker test is **not** isolation verification. `make task-image` builds the fixed offline executor. `make recover` marks stale worker attempts as infrastructure failures; it does not grant a second repair loop. Do not use a public multi-tenant deployment without further hardening.

## Structure

- `backend/app`: FastAPI, persistence, metrics, gateway, worker, sandbox and recovery.
- `backend/migrations`: Alembic schema; records store versioned typed JSON snapshots.
- `frontend/src`: responsive React/TypeScript UI, Tailwind and Recharts.
- `tasks/<id>`: manifest, starter, public/hidden/regression cases and reference.
- `scripts`: trusted container runner, local launcher and verification/scanning.
- `backend/tests`, `frontend/e2e`: security, API, persistence, metrics and browser checks.

Add a task by following an existing manifest and its case format; add all required case categories, clear requirements and a reference, then extend fixture validation. Only `solution.py` is editable in v1. Other languages require a separately built runner/image, typed tool policy and trusted evaluator; they are not currently supported. Add agent strategies by updating the strategy registry and explicit worker policy, not only UI labels.

## Limitations

See SECURITY.md and BENCHMARK_METHODOLOGY.md. This MVP is local-only, has no user auth and uses compact JSON persistence rather than a fully normalized research schema. Logs/diffs are bounded local artifact files, referenced by database records. The comparison screen includes success/duration bars, a cost scatter plot when data exists, and a task-evidence matrix. Worker concurrency (1–4) is configurable in Settings when using `make start`. Automatic infrastructure retry scheduling remains incomplete; retries default to zero. Saved agent configurations support save/edit/duplicate/use; strategy and model comparison modes share equal budgets. Stale recovery is explicit. Docker and live gateway behavior require actual integration verification; do not infer it from mocked tests.

On Macs with an unrelated unaccepted Xcode license, `/Library/Developer/CommandLineTools/usr/bin/make` can run the Makefile directly without changing Xcode licensing.

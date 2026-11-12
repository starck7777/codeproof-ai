# Final test report

Generated: 2026-11-12T18:29:26.157058+00:00
Base revision: ac60f7ab980f6a79d428a0008a54da2561515892; uncommitted source may be included.
Tested source-tree SHA256 (excluding this report and ignored runtime output): `bb0879e993b903e137fd7b942d227ce5452f84764c45f0864286d5c95a981348`

This is execution evidence, not a completion certificate. BLOCKED required checks make `make verify` fail.

| Check | Result |
|---|---|
| Disposable verification infrastructure | PASS |
| Offline task image | PASS |
| Python lint | PASS |
| Python formatting | PASS |
| Frontend lint | PASS |
| Frontend formatting | PASS |
| Backend and migration tests | PASS |
| Frontend production build and TypeScript | PASS |
| Source security scan (medium+ gate; low findings reviewed in SECURITY.md) | PASS |
| Dependency scan Python | PASS |
| Dependency scan npm | PASS |
| Secret and history scan | PASS |
| Browser exploration and offline states | PASS |
| Docker fixtures and isolation | PASS |
| Full browser benchmark workflow | PASS |

## Commands and execution evidence

### Disposable verification infrastructure: PASS

`docker compose -p codeproof-verify-568d7cfb68 -f docker-compose.verify.yml up -d --wait`

```text
 Network codeproof-verify-568d7cfb68_default Creating
 Network codeproof-verify-568d7cfb68_default Creating
 Network codeproof-verify-568d7cfb68_default Created
 Network codeproof-verify-568d7cfb68_default Created
 Container codeproof-verify-568d7cfb68-redis-1 Creating
 Container codeproof-verify-568d7cfb68-db-1 Creating
 Container codeproof-verify-568d7cfb68-redis-1 Created
 Container codeproof-verify-568d7cfb68-db-1 Created
 Container codeproof-verify-568d7cfb68-redis-1 Starting
 Container codeproof-verify-568d7cfb68-db-1 Starting
 Container codeproof-verify-568d7cfb68-redis-1 Started
 Container codeproof-verify-568d7cfb68-db-1 Started
 Container codeproof-verify-568d7cfb68-db-1 Waiting
 Container codeproof-verify-568d7cfb68-redis-1 Waiting
 Container codeproof-verify-568d7cfb68-redis-1 Healthy
 Container codeproof-verify-568d7cfb68-db-1 Healthy

```

### Offline task image: PASS

`docker build -f Dockerfile.task -t codeproof-task:1 .`

```text
#0 building with "desktop-linux" instance using docker driver

#1 [internal] load build definition from Dockerfile.task
#1 transferring dockerfile: 195B done
#1 DONE 0.0s

#2 [internal] load metadata for docker.io/library/python:3.12.8-slim
#2 DONE 1.0s

#3 [internal] load .dockerignore
#3 transferring context: 165B done
#3 DONE 0.0s

#4 [internal] load build context
#4 transferring context: 2.05kB done
#4 DONE 0.0s

#5 [1/2] FROM docker.io/library/python:3.12.8-slim@sha256:2199a62885a12290dc9c5be3ca0681d367576ab7bf037da120e564723292a2f0
#5 resolve docker.io/library/python:3.12.8-slim@sha256:2199a62885a12290dc9c5be3ca0681d367576ab7bf037da120e564723292a2f0 done
#5 CACHED

#6 [2/2] COPY scripts/container_runner.py /runner.py
#6 DONE 0.0s

#7 exporting to image
#7 exporting layers 0.0s done
#7 exporting manifest sha256:076ccd70f2d9dfd1f6acbb45ddd1a2ddddbb91bd30a0838504dde95d6d62fd71 done
#7 exporting config sha256:7277c88f005dab79e122dd50a84cf45fb4e4aa837f771dbb36c1090b6b939374 done
#7 exporting attestation manifest sha256:2ab9a0bee1cf96304c3f486f7eaad497ba375136addfe4a21e3b266592f1c7de done
#7 exporting manifest list sha256:e6075a6dbf0656bc96dc0e7ca5ddbcebb20f4692504e0369cd4ae0e270da03cc done
#7 naming to docker.io/library/codeproof-task:1 done
#7 unpacking to docker.io/library/codeproof-task:1 done
#7 DONE 0.0s

```

### Python lint: PASS

`.venv/bin/ruff check backend scripts`

```text
All checks passed!

```

### Python formatting: PASS

`.venv/bin/ruff format --check backend scripts`

```text
26 files already formatted

```

### Frontend lint: PASS

`npm run lint --prefix frontend`

```text

> codeproof-ai@0.1.0 lint
> eslint src


```

### Frontend formatting: PASS

`npm run format:check --prefix frontend`

```text

> codeproof-ai@0.1.0 format:check
> prettier --check src

Checking formatting...
All matched files use Prettier code style!

```

### Backend and migration tests: PASS

`.venv/bin/pytest -q -m not docker`

```text
.............................                                            [100%]
=============================== warnings summary ===============================
.venv/lib/python3.14/site-packages/fastapi/testclient.py:1
  [workspace]/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
29 passed, 4 deselected, 1 warning in 1.72s

```

### Frontend production build and TypeScript: PASS

`npm run build --prefix frontend`

```text

> codeproof-ai@0.1.0 build
> tsc -b && vite build

vite v6.4.6 building for production...
transforming...
✓ 1995 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.41 kB │ gzip:   0.29 kB
dist/assets/index-N6xGoqQn.css   18.39 kB │ gzip:   5.00 kB
dist/assets/index-95ze4b0L.js   631.97 kB │ gzip: 180.51 kB
✓ built in 1.59s

(!) Some chunks are larger than 500 kB after minification. Consider:
- Using dynamic import() to code-split the application
- Use build.rollupOptions.output.manualChunks to improve chunking: https://rollupjs.org/configuration-options/#output-manualchunks
- Adjust chunk size limit for this warning via build.chunkSizeWarningLimit.

```

### Source security scan (medium+ gate; low findings reviewed in SECURITY.md): PASS

`.venv/bin/bandit -r backend/app scripts -ll`

```text
Run started:2026-11-12 18:28:27.409374+00:00

Test results:
	No issues identified.

Code scanned:
	Total lines of code: 1534
	Total lines skipped (#nosec): 0
	Total potential issues skipped due to specifically being disabled (e.g., #nosec BXXX): 1

Run metrics:
	Total issues (by severity):
		Undefined: 0
		Low: 36
		Medium: 0
		High: 0
	Total issues (by confidence):
		Undefined: 0
		Low: 0
		Medium: 0
		High: 36
Files skipped (0):
[main]	INFO	profile include tests: None
[main]	INFO	profile exclude tests: None
[main]	INFO	cli include tests: None
[main]	INFO	cli exclude tests: None
[main]	INFO	running on Python 3.14.2

```

### Dependency scan Python: PASS

`.venv/bin/pip-audit -r requirements.lock`

```text
No known vulnerabilities found

```

### Dependency scan npm: PASS

`npm audit --prefix frontend --audit-level=low`

```text
found 0 vulnerabilities

```

### Secret and history scan: PASS

`.venv/bin/python scripts/scan_secrets.py`

```text
No candidate secrets detected in publishable source or existing Git history; this is not a guarantee.

```

### Browser exploration and offline states: PASS

`npm run test:e2e --prefix frontend -- --grep exploration`

```text

> codeproof-ai@0.1.0 test:e2e
> playwright test --grep exploration


Running 1 test using 1 worker

  ✓  1 e2e/app.spec.ts:2:1 › exploration: tasks, configuration, keyboard and narrow viewport (1.1s)

  1 passed (3.3s)
(node:6677) [DEP0205] DeprecationWarning: `module.register()` is deprecated. Use `module.registerHooks()` instead.
(Use `node --trace-deprecation ...` to show where the warning was created)
[2m[WebServer] [22mINFO:     Started server process [6680]
[2m[WebServer] [22mINFO:     Waiting for application startup.
[2m[WebServer] [22mINFO:     Application startup complete.
[2m[WebServer] [22mINFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
[2m[WebServer] [22m(node:6706) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
[2m[WebServer] [22m(Use `node --trace-warnings ...` to show where the warning was created)
(node:6708) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
(Use `node --trace-warnings ...` to show where the warning was created)
(node:6708) [DEP0205] DeprecationWarning: `module.register()` is deprecated. Use `module.registerHooks()` instead.
(node:6708) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
(Use `node --trace-warnings ...` to show where the warning was created)

```

### Docker fixtures and isolation: PASS

`.venv/bin/pytest -q -m docker`

```text
....                                                                     [100%]
=============================== warnings summary ===============================
.venv/lib/python3.14/site-packages/fastapi/testclient.py:1
  [workspace]/.venv/lib/python3.14/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
4 passed, 29 deselected, 1 warning in 34.86s

```

### Full browser benchmark workflow: PASS

`npm run test:e2e --prefix frontend -- --grep real evaluator`

```text

> codeproof-ai@0.1.0 test:e2e
> playwright test --grep real evaluator


Running 2 tests using 1 worker

  ✓  1 e2e/app.spec.ts:45:1 › real evaluator: benchmark, refresh, patch, compare, export (4.0s)
  ✓  2 e2e/app.spec.ts:89:1 › real evaluator: budget exhaustion and cancellation are persistent (2.0s)

  2 passed (8.1s)
(node:6920) [DEP0205] DeprecationWarning: `module.register()` is deprecated. Use `module.registerHooks()` instead.
(Use `node --trace-deprecation ...` to show where the warning was created)
[2m[WebServer] [22mINFO:     Started server process [6923]
[2m[WebServer] [22mINFO:     Waiting for application startup.
[2m[WebServer] [22mINFO:     Application startup complete.
[2m[WebServer] [22mINFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
[2m[WebServer] [22m(node:6947) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
[2m[WebServer] [22m(Use `node --trace-warnings ...` to show where the warning was created)
(node:6955) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
(Use `node --trace-warnings ...` to show where the warning was created)
(node:6955) [DEP0205] DeprecationWarning: `module.register()` is deprecated. Use `module.registerHooks()` instead.
(node:6955) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
(Use `node --trace-warnings ...` to show where the warning was created)

```

## Security findings and fixes

Initial npm findings were resolved by upgrading Vite/PostCSS and overriding vulnerable minimatch. Unsafe fixed runner temporary names were replaced with OS-generated names. The one B108 annotation covers a container-private tmpfs mount; source scan low subprocess findings are reviewed in SECURITY.md, not evidence of zero risk. History is scanned as whole files to preserve scanner context; no existing history was rewritten. Live credential/spending checks were not bypassed.

## Limitations and skipped checks

Live gateway calls: not run; no credentials and no authorized spending amount. No demo result substitutes for live integration.
Docker-dependent execution, cancellation, recovery and evaluator browser flow must pass on a Docker-equipped host. Read SECURITY.md for reviewed source scan findings and the local-only threat model.
GitHub upload/CI status is separate from these local checks. No public deployment is claimed.

## Reproduce

`make setup && make verify` on a Docker-equipped machine. Logs are local-only under `.local/verification/`. No user database is reset by verification.

## Full-stack launcher smoke check

Observed at 2026-11-12T18:31:46.420687+00:00. Command: `/Library/Developer/CommandLineTools/usr/bin/make start` (macOS Command Line Tools Make, avoiding unrelated Xcode license configuration). PostgreSQL, Redis, API, worker and frontend reached readiness.

Deterministic Demo Replay run `6735f70c60eb4e7cb522fd725f67e457` executed on the Compose stack; these are scripted outcomes, not live model measurements. JSON export returned HTTP 200.

| Strategy | Status | Strict success | Hidden passed / total |
|---|---|---|---|
| DirectPatch | Completed | True | 2 / 2 |
| IterativeFix | Completed | False | 1 / 2 |
| PlanVerify | Completed | True | 2 / 2 |

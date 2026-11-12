# Final test report

Generated: 2026-11-12T18:40:55.167901+00:00
Base revision: 81d4cd8d475c0f6e69727f3b6ee98b2d074818a9; uncommitted source may be included.
Tested source-tree SHA256 (excluding this report and ignored runtime output): `18a1471fdaa99e3292713e6089e37ee3ebdf6811f5f2f119e18a14fa1abffec1`

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

`docker compose -p codeproof-verify-f7c14a8bff -f docker-compose.verify.yml up -d --wait`

```text
 Network codeproof-verify-f7c14a8bff_default Creating
 Network codeproof-verify-f7c14a8bff_default Creating
 Network codeproof-verify-f7c14a8bff_default Created
 Network codeproof-verify-f7c14a8bff_default Created
 Container codeproof-verify-f7c14a8bff-redis-1 Creating
 Container codeproof-verify-f7c14a8bff-db-1 Creating
 Container codeproof-verify-f7c14a8bff-redis-1 Created
 Container codeproof-verify-f7c14a8bff-db-1 Created
 Container codeproof-verify-f7c14a8bff-redis-1 Starting
 Container codeproof-verify-f7c14a8bff-db-1 Starting
 Container codeproof-verify-f7c14a8bff-db-1 Started
 Container codeproof-verify-f7c14a8bff-redis-1 Started
 Container codeproof-verify-f7c14a8bff-db-1 Waiting
 Container codeproof-verify-f7c14a8bff-redis-1 Waiting
 Container codeproof-verify-f7c14a8bff-db-1 Healthy
 Container codeproof-verify-f7c14a8bff-redis-1 Healthy

```

### Offline task image: PASS

`docker build -f Dockerfile.task -t codeproof-task:1 .`

```text
#0 building with "desktop-linux" instance using docker driver

#1 [internal] load build definition from Dockerfile.task
#1 transferring dockerfile: 195B done
#1 DONE 0.0s

#2 [auth] library/python:pull token for registry-1.docker.io
#2 DONE 0.0s

#3 [internal] load metadata for docker.io/library/python:3.12.8-slim
#3 DONE 1.4s

#4 [internal] load .dockerignore
#4 transferring context: 165B done
#4 DONE 0.0s

#5 [internal] load build context
#5 transferring context: 2.05kB done
#5 DONE 0.0s

#6 [1/2] FROM docker.io/library/python:3.12.8-slim@sha256:2199a62885a12290dc9c5be3ca0681d367576ab7bf037da120e564723292a2f0
#6 resolve docker.io/library/python:3.12.8-slim@sha256:2199a62885a12290dc9c5be3ca0681d367576ab7bf037da120e564723292a2f0 done
#6 DONE 0.0s

#7 [2/2] COPY scripts/container_runner.py /runner.py
#7 CACHED

#8 exporting to image
#8 exporting layers done
#8 exporting manifest sha256:076ccd70f2d9dfd1f6acbb45ddd1a2ddddbb91bd30a0838504dde95d6d62fd71 done
#8 exporting config sha256:7277c88f005dab79e122dd50a84cf45fb4e4aa837f771dbb36c1090b6b939374 done
#8 exporting attestation manifest sha256:08ef6d84f795a07e03aaff1689f64bb76b100c6467483039caeda11428692b3c done
#8 exporting manifest list sha256:8c50ef9215009b097abb2abb0e4262b83cd0e7eda605805cff966b348ff1019e done
#8 naming to docker.io/library/codeproof-task:1 done
#8 unpacking to docker.io/library/codeproof-task:1 done
#8 DONE 0.0s

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
dist/assets/index-BUmievwo.js   632.24 kB │ gzip: 180.58 kB
✓ built in 1.62s

(!) Some chunks are larger than 500 kB after minification. Consider:
- Using dynamic import() to code-split the application
- Use build.rollupOptions.output.manualChunks to improve chunking: https://rollupjs.org/configuration-options/#output-manualchunks
- Adjust chunk size limit for this warning via build.chunkSizeWarningLimit.

```

### Source security scan (medium+ gate; low findings reviewed in SECURITY.md): PASS

`.venv/bin/bandit -r backend/app scripts -ll`

```text
Run started:2026-11-12 18:39:46.593364+00:00

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

  1 passed (3.5s)
(node:11374) [DEP0205] DeprecationWarning: `module.register()` is deprecated. Use `module.registerHooks()` instead.
(Use `node --trace-deprecation ...` to show where the warning was created)
[2m[WebServer] [22mINFO:     Started server process [11377]
[2m[WebServer] [22mINFO:     Waiting for application startup.
[2m[WebServer] [22mINFO:     Application startup complete.
[2m[WebServer] [22mINFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
[2m[WebServer] [22m(node:11403) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
[2m[WebServer] [22m(Use `node --trace-warnings ...` to show where the warning was created)
(node:11409) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
(Use `node --trace-warnings ...` to show where the warning was created)
(node:11409) [DEP0205] DeprecationWarning: `module.register()` is deprecated. Use `module.registerHooks()` instead.
(node:11409) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
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
4 passed, 29 deselected, 1 warning in 34.92s

```

### Full browser benchmark workflow: PASS

`npm run test:e2e --prefix frontend -- --grep real evaluator`

```text

> codeproof-ai@0.1.0 test:e2e
> playwright test --grep real evaluator


Running 2 tests using 1 worker

  ✓  1 e2e/app.spec.ts:45:1 › real evaluator: benchmark, refresh, patch, compare, export (6.3s)
  ✓  2 e2e/app.spec.ts:90:1 › real evaluator: budget exhaustion and cancellation are persistent (2.0s)

  2 passed (10.6s)
(node:11614) [DEP0205] DeprecationWarning: `module.register()` is deprecated. Use `module.registerHooks()` instead.
(Use `node --trace-deprecation ...` to show where the warning was created)
[2m[WebServer] [22mINFO:     Started server process [11617]
[2m[WebServer] [22mINFO:     Waiting for application startup.
[2m[WebServer] [22mINFO:     Application startup complete.
[2m[WebServer] [22mINFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
[2m[WebServer] [22m(node:11648) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
[2m[WebServer] [22m(Use `node --trace-warnings ...` to show where the warning was created)
(node:11656) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
(Use `node --trace-warnings ...` to show where the warning was created)
(node:11656) [DEP0205] DeprecationWarning: `module.register()` is deprecated. Use `module.registerHooks()` instead.
(node:11656) Warning: The 'NO_COLOR' env is ignored due to the 'FORCE_COLOR' env being set.
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

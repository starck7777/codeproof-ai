# Troubleshooting

- Docker unavailable: install/start Docker Desktop. `docker info` must succeed and `make task-image` must build. Never enable host execution as a workaround.
- Image not found or infrastructure failure: build `codeproof-task:1` on the same Docker engine the worker uses. Inspect trusted operator logs; candidate outputs are intentionally sanitized.
- Redis/database unavailable: `docker compose ps`, `docker compose logs db redis`; check loopback ports and environment. Queue port is 6379; DB 5432.
- Queued indefinitely: start `make worker` with the same database/Redis as API. Do not start the worker on the SQLite exploration database unless explicitly testing that isolated configuration.
- Interrupted worker: run `make recover` after the stale interval. It records infrastructure failure, without another agent repair loop. Restart worker for remaining queued jobs.
- Gateway failure: check Bifrost provider/model configuration, exact origin allowlist, virtual key and optional inference auth header. Do not paste keys into browser fields or logs.
- Budget exhausted: reduce task selection or increase equal per-attempt budgets. Missing usage prevents fair token enforcement, so aborts live execution.
- Port already occupied: do not kill unrelated applications. Choose available ports and update frontend proxy, backend host/origin allowlist, Compose mapping and documentation together.
- SSE disconnect: UI reconnects to a persisted full snapshot; refresh restores the last selected run. No hidden-test feedback enters the repair loop.
- GitHub auth invalid: `gh auth login -h github.com -w`; complete device authorization yourself. Never paste credentials into chat. Upload is not deployment.
- Verification nonzero: open FINAL_TEST_REPORT.md and `.local/verification/*.log`; missing required infrastructure stays blocked. Do not disable tests to obtain green status.

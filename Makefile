.PHONY: setup dev up down stop seed worker verify test task-image recover reset-help
setup:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.lock
	npm ci --prefix frontend
	npm exec --prefix frontend playwright install chromium
seed:
	PYTHONPATH=backend .venv/bin/alembic -c backend/alembic.ini upgrade head
	PYTHONPATH=backend .venv/bin/python -m app.seed
dev:
	.venv/bin/python scripts/dev.py
stop:
	.venv/bin/python -c 'import os,signal,pathlib; p=pathlib.Path(".local/dev.pid"); os.kill(int(p.read_text()),signal.SIGTERM) if p.exists() else print("No owned dev process")'
task-image:
	docker build -f Dockerfile.task -t codeproof-task:1 .
up: task-image
	mkdir -p artifacts
	LOCAL_UID=$$(id -u) LOCAL_GID=$$(id -g) docker compose up -d --build
	@echo 'Start frontend: npm run dev --prefix frontend; worker: make worker'
down:
	docker compose down
worker:
	DATABASE_URL=postgresql+psycopg://codeproof:codeproof-local-demo@127.0.0.1/codeproof REDIS_URL=redis://127.0.0.1:6379/0 PYTHONPATH=backend .venv/bin/python -m app.worker # pragma: allowlist secret - public local-only demo password
verify:
	.venv/bin/python scripts/verify.py
test:
	.venv/bin/pytest -q
reset-help:
	@echo 'No destructive reset is provided. For disposable data use a separate DATABASE_URL and Compose project name.'

recover:
	DATABASE_URL=postgresql+psycopg://codeproof:codeproof-local-demo@127.0.0.1/codeproof REDIS_URL=redis://127.0.0.1:6379/0 PYTHONPATH=backend .venv/bin/python -m app.recovery # pragma: allowlist secret - public local-only demo password

start:
	.venv/bin/python scripts/start.py
stop-all:
	.venv/bin/python -c 'import os,signal,pathlib;p=pathlib.Path(".local/stack.pid");os.kill(int(p.read_text()),signal.SIGTERM) if p.exists() else print("No owned stack supervisor")'

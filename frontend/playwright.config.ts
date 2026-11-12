import {defineConfig} from '@playwright/test';
import {mkdtempSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
const db=process.env.CODEPROOF_E2E_DATABASE_URL||'sqlite:///'+join(mkdtempSync(join(tmpdir(),'codeproof-e2e-')),'browser.db');
const env={ARTIFACT_ROOT:mkdtempSync(join(tmpdir(),'codeproof-artifacts-')),DATABASE_URL:db,PYTHONPATH:'backend',REDIS_URL:process.env.CODEPROOF_E2E_REDIS_URL||'redis://127.0.0.1:6379/14'};
export default defineConfig({testDir:'./e2e',timeout:30000,use:{baseURL:'http://127.0.0.1:5173',headless:true,channel:process.env.CODEPROOF_BROWSER_CHANNEL||'chromium'},webServer:[{command:'cd .. && .venv/bin/python -m app.seed && .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000',env,url:'http://127.0.0.1:8000/api/health',reuseExistingServer:false},{command:'npm run dev -- --port 5173 --strictPort',url:'http://127.0.0.1:5173',reuseExistingServer:false},...(process.env.CODEPROOF_FULL_E2E==='1'?[{command:'cd .. && .venv/bin/python -m app.worker',env,wait:{stdout:/Listening on/},timeout:30000}]:[])]});

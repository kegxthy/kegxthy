# 部署 / Deployment

[中文 README](README.md) · [English README](README_EN.md)

## Local / 本地

Install Python 3.12 and `requirements.txt`. Set a random 32–256 character ASCII `FINGUARD_ACCESS_TOKEN` (required even on localhost) and `LLM_API_KEY` or `DEEPSEEK_API_KEY` privately in the shell. Optional `LLM_MODEL` defaults to `deepseek-flash`; only the official DeepSeek endpoint is approved. Run from `finguard-ai/`:

```bash
python -m uvicorn server:app --host 127.0.0.1 --port 8000 --workers 1
```

PowerShell 私密输入密钥（不会回显），然后启动：

```powershell
$env:FINGUARD_ACCESS_TOKEN = python -c "import secrets; print(secrets.token_urlsafe(32))"
$secret = Read-Host 'DeepSeek API key' -AsSecureString
$env:LLM_API_KEY = [System.Net.NetworkCredential]::new('', $secret).Password
python -m uvicorn server:app --host 127.0.0.1 --port 8000 --workers 1
```

On macOS/Linux, set the environment through your secret manager or a private shell session. `.env.example` only documents names; the app does not automatically load `.env`. Never paste secrets into tracked files.

## Docker

```bash
docker compose up --build
```

Compose requires shell variables `LLM_API_KEY` and a random `FINGUARD_ACCESS_TOKEN`. Open http://127.0.0.1:7860 and enter the workspace token. Data lives in the `finguard-data` named volume. Docker exposes loopback only by default. Back up SQLite through its backup API before removing volumes. The image runs as a non-root user; keep one worker.

先设置密钥和随机工作区令牌，再运行 Compose。默认仅绑定本机。公开访问需要 TLS、正确代理配置和受控用户入口。当前会话无 Docker 引擎，未声称镜像构建验证成功。

## Render Blueprint

Use the repository branch `feat/finguard-agent-v1` and Blueprint path `finguard-ai/render.yaml`. Review the resource changes in Render before applying. The existing service name `finguard-ai` is retained; confirm it identifies the intended FinGuard service before sync. Do not sync it over another project.

The Blueprint uses native Python, `rootDir: finguard-ai`, `server:app`, one worker, `/health`, a generated workspace token and `LLM_API_KEY` entered through Render's secret configuration. `autoDeployTrigger: "off"` prevents automatic deployments while the PR is under review. No API key is stored in YAML.

SQLite uses `/var/data/tasks.sqlite3` on a 1 GB persistent disk. A paid web-service compute plan is required. The plan is deliberately not pinned: inspect the existing service/default paid plan and costs in Render before creating/syncing. One disk means one instance; redeploys interrupt service and active jobs become failed. No horizontal scaling or zero-downtime promise.

在 Render 新建 Blueprint 时选择上述路径与分支，填入真实 `LLM_API_KEY`，私下保存生成的 `FINGUARD_ACCESS_TOKEN`，确认费用与服务归属后应用。已有服务更新时，`sync:false` 不会再次提示密钥；需在 Environment 页面设置并重新部署。不可用 GitHub Pages 运行 Python 分析后端。

References: [Blueprint specification](https://render.com/docs/blueprint-spec), [persistent disks](https://render.com/docs/disks), [environment variables](https://render.com/docs/configure-environment-variables). The YAML is validated against the official [JSON Schema](https://render.com/schema/render.yaml.json); schema validity does not prove resource availability or deployment success.

## Deployment acceptance / 部署验收

1. Record the actual HTTPS service URL and deployed commit SHA.
2. `GET /health` must return 200 and indicate model/access readiness. This is configuration readiness, not a live model probe.
3. Unauthenticated `/api/tasks` must return 401. In the UI, enter the private workspace token.
4. Upload an authorized public report, explicitly approve DeepSeek, and observe actual extraction logs.
5. Confirm correct source-backed consolidated figures, one period/currency; verify ratios independently.
6. Wait for a completed task, inspect tools/evidence, download PDF and inspect Chinese/English glyphs.
7. Restart the service and verify history persists, review tasks can continue, and interrupted jobs are labeled failed.
8. Delete the acceptance task when finished. Do not publish provider keys, tokens or confidential source data in screenshots/logs.

Do not mark deployment complete if any gate is untested. See [VALIDATION.md](docs/VALIDATION.md) for the current evidence and remaining gates.

## Retention / 清理与备份

`FINGUARD_MODE=workspace` is the default and requires authentication for all API calls. `public_demo` only shows UI, disables all APIs and does not open a workspace database. Never treat a shared team token as public-user authentication.

`FINGUARD_RETENTION_HOURS=24` defaults to a 24-hour creation-based TTL; valid range 1–168. Expired records are removed at startup, during API access and every minute; an active phase is allowed to finish before cleanup. Complete extracted sources are removed immediately after confirmation or failure. API responses contain evidence lines only. Startup also scrubs full sources from legacy terminal records.

Run maintenance while the application is stopped (it does not share active-job leases across processes):

```bash
python maintenance.py cleanup
python maintenance.py backup --destination /private/backup/finguard-unique-name.sqlite3
```

Backup refuses overwriting an existing file and uses SQLite's online backup API. To restore, stop the application, preserve the current database privately, place a verified backup at FINGUARD_DB and restart. Verify task state/expiry/auth; interrupted tasks become failed. Restrict backup access and apply a separate backup TTL. Task deletion/secure_delete does not erase backup copies or provider retention.

## 阿里云函数计算（实际目标） / Actual target: Alibaba FC

The user confirmed the existing backend is FC in Hangzhou, custom Node.js 20, port 9000, not ECS. Follow [ALIYUN_FC.md](docs/ALIYUN_FC.md). Do not SSH, overwrite the existing Node function, claim /health validates FinGuard, or upload this Python directory as if it supplied durable FC storage/dispatch. The Render configuration above is an optional alternative, not the selected deployment target.

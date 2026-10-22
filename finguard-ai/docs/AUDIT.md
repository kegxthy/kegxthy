# Initial audit / 初始代码审计

Baseline: `b3d81e16276002395bf6a28044631a5a39cb799f`, branch `feat/finguard-agent-v1`.
All original files, including hidden `.env.example`, were read before their replacement or retention decision. No repository AGENTS.md was found. Scope is exclusively `finguard-ai/`.

- `app.py`: keep as legacy regression reference. Explicit key=value parsing and rule concepts inform the new Decimal implementation. It remains independently runnable but is not the V1 deployment target.
- `index.html`: retain legacy page; its illustrative sample is not used by V1.
- `server.py`: refactor alternate FastAPI entrypoint into persistent task API, consent gate and confirmation workflow. Previous in-memory synchronous report contract is deliberately migrated to asynchronous 202 responses.
- `agent_service.py`: retain old chunk summarizer/PDF code as reference; V1 does not import it. Original prompt-only citation promises were insufficient to establish source fidelity.
- `workspace.html`: refactor to bilingual review workspace, real polling/events, evidence, history and authenticated exports. Preserve same-origin serving and escaped text rendering.
- `requirements.txt`: retain dependencies required by both paths; pin tested direct versions. Add separate test dependencies.
- `Dockerfile`: retain container entrypoint; move to Python 3.12, non-root user and single worker.
- `render.yaml`: fix `app:app` mismatch, set monorepo root, feature branch, server-side secrets and persistent SQLite disk. Auto deploy disabled.
- `.env.example`: replace stale OpenAI/DeepSeek mixed configuration with the approved DeepSeek-only V1 settings; no secret values.
- `README.md`, `README_DEPLOY.md`: replace conflicting MVP setup instructions with Chinese/English V1 documentation and explicit compatibility/validation limits.

No existing original file was deleted. No other project or repository root file is changed. New services separate parsing/model orchestration (`workflow.py`), arithmetic/rules/evidence (`finance.py`), SQLite (`task_store.py`), PDF (`export_pdf.py`) and API lifecycle (`server.py`).

MoneyPrinterTurbo's actual README was reviewed for clear language links, capability lists, setup/deployment sections and modular API/UI/CLI organization. FinGuard uses its own implementation; its domain does not require copying video-processing dependencies.

# ✦ FinGuard AI

**Explainable Financial Risk Analysis Agent · Snow's Agent Lab**

A real FastAPI application with a white / misty-blue / blush-pink / cool-gray dashboard, deterministic financial calculations, traceable screening rules, PDF/XLSX ingestion and optional DeepSeek / GPT explanations.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app:app --reload
```

Open **http://localhost:8000**. Try the built-in illustrative sample; no API key required.

For real LLM explanations, set server-side environment variables (never expose a key in frontend code):

```bash
export LLM_BASE_URL=https://api.deepseek.com
export LLM_MODEL=deepseek-chat
export LLM_API_KEY=your_key_here
```

OpenAI alternative: `LLM_BASE_URL=https://api.openai.com/v1`, `LLM_MODEL=gpt-4.1-mini` (choose an available model).

## Workflow

`Upload → Parse → Extract explicit fields → Calculate ratios → Detect risk signals → Optional LLM explanation → Human review → Export JSON`

**Important scope:** This is a working **MVP**, not a production-ready autonomous financial analyst. For arbitrary annual reports, this version extracts text but requires fields normalized to `key=value` for deterministic calculation. Scanned PDFs need OCR; complex tables need extraction validation. No fabricated metrics, no automatic Z-score, no unsupported financial ratings. Screening thresholds are illustrative.

### Sample fields

`revenue, net_profit, operating_cash_flow, accounts_receivable, current_assets, current_liabilities, total_assets, total_liabilities`.

## API

- `GET /health` checks server configuration.
- `POST /api/analyze` accepts JSON `{\"company\":\"Demo\",\"text\":\"revenue=12000\\n...\",\"use_llm\":false}`.
- `POST /api/upload` accepts multipart PDF/XLSX/TXT/CSV up to 8 MB.

## Deployment

**GitHub Pages cannot host the Python backend.** Deploy this directory as a Python web service on Render, Railway or a similar host with start command `uvicorn app:app --host 0.0.0.0 --port $PORT`. Set environment variables in the hosting provider. Do not put private annual reports into a public demo. Production needs auth, encryption, retention policy, request limits, and an extraction review UI.

## Roadmap

1. Page/cell-level source evidence and human correction queue.
2. Schema-validated LLM extraction with consistency checks.
3. Persisted LangGraph workflow with interrupt/resume and evaluation set.
4. Authenticated multi-tenant deployment, observability and audit log.

Original 2025 coursework used a mocked DeepSeek module; this repository is a new implementation inspired by that workflow, not a claim that the old prototype was production deployed.

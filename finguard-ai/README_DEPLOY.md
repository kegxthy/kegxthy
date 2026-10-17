# FinGuard AI v0.2 · DeepSeek annual-report agent
A real backend-powered report-analysis MVP, separate from the static GitHub Pages demo.

## What works
- Upload text-based PDF or DOCX (12 MB / 120 PDF pages maximum)
- Extract text with PyMuPDF / python-docx
- Chunk documents and call DeepSeek Chat using a server-side secret
- Consolidate chunk notes into a structured JSON report with risk findings and evidence markers
- Preview report and download generated PDF
- Optional user prompt appended under non-overridable evidence/safety rules

## Run locally
```bash
cd finguard-ai
pip install -r requirements.txt
export LLM_API_KEY=your_deepseek_api_key
export LLM_BASE_URL=https://api.deepseek.com
export LLM_MODEL=deepseek-chat
uvicorn server:app --reload
```
Open http://127.0.0.1:8000 .

## Host publicly (Hugging Face Docker Space)
Create a Docker Space, upload the contents of this directory to the Space root, and add `LLM_API_KEY` under **Settings → Variables and secrets → Secrets**. Container listens on 7860. Link the Space URL from GitHub.

## Important limitations
- GitHub Pages alone cannot execute this backend.
- No OCR for scanned PDFs. Tables in PDFs may extract poorly.
- A long document may exceed the 24-chunk demo budget.
- JSON is validated for shape, not independently verified against source evidence. Citations are model-generated and require human review.
- No authentication, job queue, per-user isolation, durable storage, rate limiting, billing budget, or virus scanning: **do not expose this MVP to untrusted public traffic with a paid API key** until these controls are implemented.
- In-memory reports disappear on restart. Do not upload confidential financial documents.
- Chinese PDF export font fallback needs validation for your deployment image and report contents.

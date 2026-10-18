# Validation record / 验证记录

Date: 2026-10-19, Asia/Shanghai. Validation is separated from deployment.

## Passed locally

- Windows, Python 3.12, isolated venv, direct dependencies pinned in `requirements.txt`; `pip check` reports no broken requirements.
- `python -m pytest tests -q`: 13 offline tests pass; the optional Chrome test is skipped unless configured.
- With `requirements-browser.txt` installed and `FINGUARD_BROWSER` set to a local Chrome executable: **14 tests pass**. One upstream Starlette warning deprecates its httpx TestClient integration; tests succeed. No performance benchmark is claimed.
- Coverage: three parsers, empty scans, invalid files, expanded ZIP limits, evidence/schema rejection, missing inputs, units, period mismatch, zero denominators, large finite Decimal ratios, exact threshold boundaries, cash divergence, bounded tools, unknown-tool/iteration rejection, provider transport contract, confirmation, history persistence, token checks, failure redaction and PDF smoke.
- Real Chrome E2E: Chinese/English switching and persistence, authenticated upload of an explicitly labeled test fixture, real HTTP task polling, human confirmation, mocked-provider tool dispatch, ratios/signals, source navigation, PDF download, responsive 390px layout and no JavaScript page errors.
- Actual local Uvicorn startup and `/health` worked. The README screenshot is a real empty workspace, not a generated image or a fake financial result.
- Current official Render JSON Schema validation passes. The YAML quotes `"off"` to prevent YAML 1.1 boolean conversion. No Render platform validation or deployment was performed.

## Actual public report, offline

Downloaded [Apple FY2024 annual report](https://www.annualreports.com/HostedData/AnnualReportArchive/a/NASDAQ_AAPL_2024.pdf).

SHA-256: `ec74758cd767465362c641cf2fd5d8fedd477aed2bf7f62117e67610435dcb88`.

`validate_public_report.py` extracted 121 nonempty source blocks and 486451 characters. On PDF page 34 (printed page 31), manually selected consolidated FY2024 current assets 152987 and current liabilities 176392 (USD millions). Exact source-line verification passed. Decimal calculation `152987 / 176392` displays **0.8673**, triggering the illustrative liquidity rule. Other ratios explicitly remain missing.

```bash
python validate_public_report.py /path/to/NASDAQ_AAPL_2024.pdf --pdf /tmp/offline-check.pdf
```

The resulting one-page bilingual PDF was rendered with PyMuPDF and visually inspected: Chinese glyphs, evidence, figures and page numbering are legible without clipping. It is clearly labeled an offline parser/math/export check. No DeepSeek call occurred; this is not end-to-end live-model acceptance. The full PDF is not committed. A short factual regression fixture is in `tests/test_public_report.py`.

## Remaining acceptance gates

- **Real DeepSeek analysis unverified**: no `LLM_API_KEY` is available in the execution environment. Structured extraction and actual tool-calling model behavior have been implemented and mocked, but not validated against the live provider. Do not mark Issue #1 fully accepted until a real approved report completes extraction, human confirmation, tool analysis and PDF download with a valid server-side key.
- **Online deployment unverified**: no service was created, synced or deployed; no live HTTPS URL exists from this work. `/health` alone would not prove analysis works. Follow every gate in `README_DEPLOY.md`, including token access, actual analysis, export and persistent history after restart.
- **Docker unverified**: this environment has no Docker engine. Compose and Dockerfile are supplied; an actual image build/run remains to be checked.
- Single-team scope, manual table semantics review and qualitative model fidelity limitations remain as documented in architecture/README. OCR, tenant isolation, distributed queue and automated backups are not implemented.

## Reproduce browser check

```powershell
python -m pip install -r requirements-browser.txt
$env:FINGUARD_BROWSER = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
python -m pytest tests -q
```

On Linux/macOS set `FINGUARD_BROWSER` to an installed Chromium/Chrome executable. All model responses in tests are explicitly mocked; no real provider key is required for tests. Live acceptance must use server configuration, never fixture mocks.

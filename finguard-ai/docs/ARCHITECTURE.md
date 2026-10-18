# Product and architecture contract / 产品与架构

## Product

Finance teams, risk analysts and research analysts upload authorized reports, confirm critical figures and review risk signals supported by source text. Chinese and English UI strings share one dictionary; localStorage stores only the language preference. The default goal is comprehensive review; cash-flow/liquidity presets and user focus are passed as untrusted data to the agent.

## Vertical workflow

`upload → local parsing → DeepSeek extraction → evidence validation → needs_review → human confirmation → Decimal calculation + rules → bounded tool agent → completed → PDF/history`

States are `extracting`, `needs_review`, `analyzing`, `completed`, `failed`. Events contain UTC timestamps and stage/tool names only, never model reasoning. No fabricated percentages. SQLite stores each transition. After restart, interrupted execution is failed explicitly; confirmation waits and completed reports survive. A user creates a new task to retry failures. Run one Uvicorn worker, one instance; this is an in-process executor with durable records, not a distributed durable queue.

## Module boundaries

- `workflow.py`: PDF/DOCX/XLSX text extraction, expansion/text/page budgets, sequential bounded chunks, DeepSeek HTTP, evidence candidates and tool loop.
- `finance.py`: strict Figure schema, source/quote/number checking, Decimal arithmetic and rule triggers. No network or model arithmetic.
- `task_store.py`: parameterized SQLite persistence, timestamps and deletion.
- `server.py`: shared-team bearer access, upload/consent, state transitions, concurrency cap, sanitized failures and restart handling.
- `export_pdf.py`: escaped text, formulas, figures, source quotes, model interpretation labels, limitations and tool trace.
- `workspace.html`: upload, consent, presets, actual logs, editable confirmation, source viewer, history and authenticated PDF download.

## Evidence schema

Source: `{id: "page:42" | "paragraph:3" | "table:2:row:4" | "sheet:Balance:row:8", text: string}`.

Figure: `{field, value, period, currency, scope, scale, source_id, line_number, number_index, quote}`. Period is a validated YYYY-MM-DD/YYYY-MM-DD reporting interval, currency a supported ISO code normalized to uppercase, scope `consolidated` or `parent`. Confirmation and all financial entrypoints require consolidated scope, one canonical context and unique fields; parent/mixed/duplicate data fails closed before tools or model calls. `value` is a finite Decimal string (maximum magnitude 1e20, maximum 12 decimal places). Allowed scales: 1, 1000, 10000, 1000000, 100000000, 1000000000. Unknown fields and extra schema properties are rejected. Quotes must exactly equal one stripped source line selected by 1-based `line_number`. The pre-number row label must match the supported financial-field lexicon. Zero-based `number_index` selects the exact numeric token, with comma/parenthesis normalization; XLSX coordinate digits are excluded. Broad page quotes and same-page wrong-field values are rejected. Unsupported row labels require parser/lexicon improvements, not a silent permissive fallback. This does not establish the correct column, currency or account meaning: human confirmation is mandatory. Corrections remain source-backed; no unanchored override.

Candidates can contain competing periods. Confirmation accepts at most eight unique fields in one period/currency. The schema requires consolidated scope at execution; users still verify that declaration against the report. Extraction omits unknown units or dates rather than guessing. No precomputed fake outcomes or risk ratings.

## Metrics and rule definitions

Four ratios: `current_assets/current_liabilities`, `total_liabilities/total_assets`, `operating_cash_flow/net_profit`, `accounts_receivable/revenue`. Values normalize scales before division. Denominators must be positive. Missing inputs and invalid denominators produce reasons, not zero values. Duplicate fields, mismatched canonical contexts, unsupported currencies and parent scope are rejected before calculation, screening, balance checks and agent entry. Display rounds to four decimals; rules compare the unrounded Decimal result.

Signals: LIQUIDITY when current ratio <1; LEVERAGE when liabilities/assets >0.70; RECEIVABLES when receivables/revenue >0.35; CASH_PROFIT_DIVERGENCE when profit >0 and operating cash flow <0 in the same period/currency. First three are medium, divergence is high screening priority. Thresholds are illustrative, sector-dependent and unvalidated as default predictors. No trigger is not an absence-of-risk finding. Balance checks flag liabilities exceeding assets without assigning a rating.

## Tool contract and trust boundaries

DeepSeek sees confirmed source-bearing figures and the user focus as data. Only `calculate_metrics`, `screen_risks`, `check_balance` are executable, with empty argument objects. At most four model rounds and three calls per round. Unknown tools, nonempty arguments, invalid JSON and exhausted iterations fail the task. HTTP timeout 60s; extraction/analysis phase timeout 600s; chunks have bounded text and output tokens. Endpoint is exactly `https://api.deepseek.com`; redirects are not followed. No shell, browser, SQL, filesystem or arbitrary URL tool is available to the model.

Only validated observation objects with existing source IDs and no Arabic digits are displayed; rejected count is visible. This is syntactic citation/numeric filtering, not semantic entailment verification. Qualitative model interpretations can still be wrong and are labeled accordingly. Deterministic ratios/rules and original quotes are displayed separately. Prompt boundaries reduce instruction injection; the tool allowlist prevents arbitrary action even if the model is influenced.

## API

Interactive request/response schemas: `/docs`, machine-readable `/openapi.json`.

- `GET /health`: liveness, model configuration and remote-access readiness. This does not call or validate the provider.
- `POST /api/tasks` (alias `/api/reports`): multipart `file`, `focus` (or legacy `prompt`), `provider_consent=true`; returns 202 plus persisted task. No implicit consent.
- `GET /api/tasks`: task summaries; `GET /api/tasks/{id}`: state, figures, evidence-line excerpts only, warnings, events, expiry and result. Full raw sources are never serialized by any task response.
- `POST /api/tasks/{id}/confirm`: JSON `{figures: Figure[]}`; 202 after review; 409 if wrong state; 422 on bad evidence, duplicates or mixed period/currency.
- `GET /api/tasks/{id}/pdf` (alias `/api/reports/{id}/pdf`): completed reports only, otherwise 409.
- `DELETE /api/tasks/{id}`: 204; active execution cannot be deleted.

Error codes: 401 missing/invalid configured token, 403 all APIs disabled in public preview, 413 file size, 415 extension, 422 consent/document/evidence validation, 429 capacity/history limit, 503 missing model key or removed/invalid runtime authentication configuration. Background errors are persisted as sanitized failure messages; provider payloads and exception text are not exposed.

## Security and deployment scope

Single trusted team shares one bearer token and all history. Confidential data is not approved merely because a model key exists: each task records explicit provider approval. No tenant isolation, RBAC, malware sandbox or encrypted application database. Treat bearer tokens as credentials; keep them out of URLs and persistent frontend storage. There is no localhost bypass: startup requires a 32–256 character ASCII workspace token, and every API request validates it regardless of peer/forwarded IP. Missing configuration after startup returns 503. Public preview mode disables every API and never opens the workspace database. It is not a public upload demo. Use TLS and server-side secrets remotely. Request/file/expanded-text limits are not a substitute for a hardened ingress and upload sandbox.

Only extracted text is retained, not source bytes. Delete tasks when finished; use SQLite-native backups, protect host disk and enforce provider policies separately. Render disk supports one instance and interrupts deploys; no horizontal scaling claim is made.

## Acceptance

Automated gates cover parsers, evidence rejection, math, thresholds, safe tool dispatch, model transport contract, API lifecycle, persistence, authorization and PDF smoke. UI is checked in a real browser. A real annual-report extraction and independently checked ratios must be recorded separately from mocked-model tests. Live acceptance additionally requires an approved server-side key, actual extraction/confirmation/tool run and downloaded PDF. Deployment acceptance requires a live HTTPS URL, authenticated analysis, health, restart history and PDF; a commit or successful build alone does not pass it.

## Retention and rollout after review

Raw extracted text exists only during extraction/review and is removed after confirmation, failure or interrupted restart. Detail/create/confirm responses expose only figure evidence lines. Candidate cap 128, quote limit 1500 characters, total stored task payload budget approximately 20 MB. Retention defaults to 24h, configurable 1–168h. Creation-based expiry is checked at startup, on API access and every minute; in-flight phases finish before deletion. SQLite secure_delete is enabled, but this does not erase backups or provider records. `maintenance.py cleanup` runs with the app stopped; `backup --destination` uses the native SQLite backup API and refuses overwrites. Backups need a separate private retention policy.

The confirmed online Alibaba FC resource is the separate Node.js Agent Lab function; it is not the Python FinGuard deployment. No SSH or ECS path applies. An independent Python FC release requires durable storage/dispatch and FC lifecycle validation, plus authorized deployment access. See ALIYUN_FC.md.

"""Regression gates for PR #2 review: proxy auth, privacy, financial context and row anchors."""

import json
import sqlite3
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from finance import Figure, verify, calculate, screen, check_balance
from task_store import Store, now
from conftest import TEST_TOKEN
from test_workflow import fig, pdf_bytes, poll
import server
import workflow

AUTH = {"Authorization": "Bearer " + TEST_TOKEN}


@pytest.mark.parametrize("peer", ["127.0.0.1", "::1", "192.0.2.10", "testclient"])
def test_missing_token_fails_startup_even_for_loopback(monkeypatch, tmp_path, peer):
    monkeypatch.delenv("FINGUARD_ACCESS_TOKEN")
    monkeypatch.setenv("FINGUARD_DB", str(tmp_path / "tasks.db"))
    with pytest.raises(RuntimeError, match="32-256"):
        with TestClient(server.app, client=(peer, 12345)):
            pass


def test_proxy_headers_cannot_bypass_auth(monkeypatch, tmp_path):
    monkeypatch.setenv("FINGUARD_DB", str(tmp_path / "tasks.db"))
    with TestClient(server.app, client=("127.0.0.1", 12345)) as client:
        for headers in (
            {},
            {"X-Forwarded-For": "127.0.0.1"},
            {"Forwarded": "for=127.0.0.1;host=localhost"},
            {"X-Forwarded-For": "198.51.100.10", "Host": "localhost"},
        ):
            assert client.get("/api/tasks", headers=headers).status_code == 401
        assert client.get("/api/tasks", headers=AUTH).status_code == 200
        monkeypatch.delenv("FINGUARD_ACCESS_TOKEN")
        assert client.get("/api/tasks", headers=AUTH).status_code == 503


def test_public_preview_cannot_read_or_upload(monkeypatch, tmp_path):
    monkeypatch.setenv("FINGUARD_DB", str(tmp_path / "tasks.db"))
    monkeypatch.setenv("FINGUARD_MODE", "public_demo")
    monkeypatch.delenv("FINGUARD_ACCESS_TOKEN")
    with TestClient(server.app) as client:
        assert server.store is None
        assert not (tmp_path / "tasks.db").exists()
        assert client.get("/health").json()["mode"] == "public_demo"
        assert client.get("/").status_code == 200
        for method, url in [
            ("get", "/api/tasks"),
            ("get", "/api/tasks/any"),
            ("get", "/api/tasks/any/pdf"),
            ("post", "/api/tasks"),
            ("post", "/api/reports"),
            ("delete", "/api/tasks/any"),
        ]:
            assert getattr(client, method)(url, headers=AUTH).status_code == 403


@pytest.mark.parametrize(
    "change",
    [
        {"period": "2025"},
        {"period": "2025-02-30/2025-12-31"},
        {"period": "2025-12-31/2025-01-01"},
        {"currency": "$"},
        {"currency": "RMB"},
        {"scope": "unknown"},
        {"scale": True},
    ],
)
def test_canonical_schema_rejects_ambiguous_context(change):
    data = fig()
    data.update(change)
    with pytest.raises(ValueError):
        Figure.model_validate(data)


def test_canonical_currency_normalization_and_scale():
    a, b = fig(), fig("current_liabilities", "100")
    a["currency"] = " usd "
    a["scale"] = 1000
    assert Figure.model_validate(a).currency == "USD"
    assert calculate([a, b])[0]["current_ratio"]["value"] == "800.0000"


@pytest.mark.parametrize(
    "function", [calculate, check_balance, lambda fs: screen(fs, {})]
)
@pytest.mark.parametrize("kind", ["duplicate", "period", "currency", "scope"])
def test_every_financial_entry_rejects_ambiguous_data(function, kind):
    a, b = fig("total_assets", "100"), fig("total_liabilities", "80")
    if kind == "duplicate":
        figures = [a, b, a]
    else:
        b.update(
            {"period": "2024-01-01/2024-12-31"}
            if kind == "period"
            else {"currency": "CNY"}
            if kind == "currency"
            else {"scope": "parent"}
        )
        figures = [a, b]
    with pytest.raises(ValueError):
        function(figures)


def test_wrong_field_right_page_and_number_is_rejected():
    source = {"id": "page:1", "text": "Revenue 80 100\nCurrent assets 80 100"}
    data = fig()
    data.update(quote="Revenue 80 100", line_number=1, number_index=0)
    assert verify([data], [source])[
        1
    ]  # Old page membership check incorrectly accepted this.
    data.update(quote="Current assets 80 100", line_number=2)
    assert verify([data], [source])[0]
    data["number_index"] = 1
    assert verify([data], [source])[1]  # Right row, wrong selected column.
    data.update(
        number_index=0, quote="Revenue 80 100\nCurrent assets 80 100", line_number=1
    )
    assert verify([data], [source])[1]  # Broad page/paragraph quote forbidden.


def test_xlsx_exact_row_anchor():
    source = {"id": "sheet:Balance:row:2", "text": "A2=Current assets | B2=80 | C2=100"}
    data = fig()
    data.update(source_id=source["id"], quote=source["text"])
    assert verify([data], [source])[0]


@pytest.mark.asyncio
async def test_agent_rejects_duplicates_before_any_provider_call(monkeypatch):
    called = False

    async def provider(*args, **kw):
        nonlocal called
        called = True
        raise AssertionError("Provider must not be called")

    async def event(message):
        pass

    monkeypatch.setattr(workflow, "completion", provider)
    with pytest.raises(ValueError, match="Duplicate"):
        await workflow.agent([fig(), fig()], "", event)
    assert not called


def test_raw_document_never_returned_and_removed_after_confirmation(
    monkeypatch, tmp_path
):
    monkeypatch.setenv("FINGUARD_DB", str(tmp_path / "tasks.db"))
    monkeypatch.setenv("LLM_API_KEY", "test-only")
    original = workflow.extract
    sentinel = "UNSELECTED_RAW_TEXT_MUST_NOT_BE_EXPOSED"

    def extract(data, name):
        return original(data, name) + [{"id": "page:999", "text": sentinel}]

    monkeypatch.setattr(workflow, "extract", extract)

    async def provider(messages, tools=None):
        return (
            {"content": '{"observations":[]}'}
            if tools
            else {
                "content": json.dumps(
                    {"figures": [fig(), fig("current_liabilities", "100")]}
                )
            }
        )

    monkeypatch.setattr(workflow, "completion", provider)
    with TestClient(server.app, headers=AUTH) as client:
        response = client.post(
            "/api/tasks",
            data={"provider_consent": "true"},
            files={"file": ("a.pdf", pdf_bytes())},
        )
        token = response.json()["id"]
        assert sentinel not in response.text
        task = poll(client, token, "needs_review")
        assert sentinel not in json.dumps(task)
        assert any(s["text"] == sentinel for s in server.store.get(token)["sources"])
        parent = fig()
        parent["scope"] = "parent"
        assert (
            client.post(
                f"/api/tasks/{token}/confirm", json={"figures": [parent]}
            ).status_code
            == 422
        )
        assert (
            client.post(
                f"/api/tasks/{token}/confirm", json={"figures": task["figures"]}
            ).status_code
            == 202
        )
        poll(client, token, "completed")
        assert server.store.get(token)["sources"] == []
        assert "Current assets 80" in client.get(f"/api/tasks/{token}").text


def test_retention_cleanup_and_backup(monkeypatch, tmp_path):
    monkeypatch.setenv("FINGUARD_DB", str(tmp_path / "tasks.db"))
    store = Store()
    created = datetime.now(timezone.utc) - timedelta(hours=25)
    old = {
        "id": "old",
        "created_at": created.isoformat(),
        "status": "needs_review",
        "sources": [{"text": "private"}],
    }
    store.save(old)
    assert (
        store.cleanup(active_ids={"old"}) == 0
    )  # Active phase may finish before deletion.
    assert store.cleanup() == 1 and store.get("old") is None
    task = {"id": "new", "created_at": now(), "status": "completed", "sources": []}
    store.save(task)
    expiry = task["expires_at"]
    store.save(task)
    assert task["expires_at"] == expiry  # Reading/updating must not extend retention.
    backup = tmp_path / "backup.db"
    store.backup(backup)
    with sqlite3.connect(backup) as db:
        assert db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 1
    with pytest.raises(ValueError):
        store.backup(backup)
    with store.connect() as db:
        assert db.execute("PRAGMA secure_delete").fetchone()[0] == 1


@pytest.mark.parametrize("value", ["short", " " * 32, "密" * 32])
def test_invalid_workspace_token_rejected(monkeypatch, tmp_path, value):
    monkeypatch.setenv("FINGUARD_ACCESS_TOKEN", value)
    monkeypatch.setenv("FINGUARD_DB", str(tmp_path / "tasks.db"))
    with pytest.raises(RuntimeError, match="32-256"):
        with TestClient(server.app):
            pass


def test_deepseek_environment_alias(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only-alias")
    assert workflow.model_key() == "test-only-alias"


@pytest.mark.asyncio
async def test_extraction_preserves_line_offsets_and_rejects_oversized_lines(
    monkeypatch,
):
    source = {"id": "page:1", "text": "x" * 16000 + "\nCurrent assets 80"}
    data = fig()
    data["line_number"] = 2

    async def provider(messages, tools=None):
        groups = json.loads(messages[1]["content"])
        assert len(groups[0]["text"]) < 16000
        assert groups[0]["text"].splitlines()[1] == "Current assets 80"
        return {"content": json.dumps({"figures": [data]})}

    async def event(message):
        pass

    monkeypatch.setattr(workflow, "completion", provider)
    figures, warnings = await workflow.extract_figures([source], event)
    assert figures[0]["line_number"] == 2 and warnings


def test_startup_cleans_expired_and_scrubs_interrupted(monkeypatch, tmp_path):
    monkeypatch.setenv("FINGUARD_DB", str(tmp_path / "tasks.db"))
    store = Store()
    for token, created, status in [
        (
            "old",
            (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
            "completed",
        ),
        ("interrupted", now(), "extracting"),
    ]:
        store.save(
            {
                "id": token,
                "created_at": created,
                "status": status,
                "sources": [{"id": "page:1", "text": "raw"}],
            }
        )
    with TestClient(server.app, headers=AUTH) as client:
        assert client.get("/api/tasks/old").status_code == 404
        assert server.store.get("interrupted")["sources"] == []
        assert server.store.get("interrupted")["status"] == "failed"

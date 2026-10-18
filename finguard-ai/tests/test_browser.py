"""Opt-in real browser E2E with an explicitly mocked provider, never production data.

pip install playwright
Set FINGUARD_BROWSER to your Chrome/Chromium executable, then pytest tests/test_browser.py.
"""

import json
import os
import socket
import threading
import time
import pytest
import uvicorn
import workflow
import server
from test_workflow import fig, pdf_bytes


@pytest.mark.skipif(
    not os.getenv("FINGUARD_BROWSER"), reason="Opt-in Chrome executable required"
)
def test_browser_upload_confirm_evidence_export(monkeypatch, tmp_path):
    from playwright.sync_api import sync_playwright, expect

    monkeypatch.setenv("FINGUARD_DB", str(tmp_path / "browser.db"))
    monkeypatch.setenv("LLM_API_KEY", "mock-provider-only")
    monkeypatch.setenv("FINGUARD_ACCESS_TOKEN", "browser-test-token-" + "b" * 32)

    async def fake(messages, tools=None):
        if not tools:
            return {
                "content": json.dumps(
                    {"figures": [fig(), fig("current_liabilities", "100")]}
                )
            }
        if any(m["role"] == "tool" for m in messages):
            return {"content": '{"observations":[]}'}
        return {
            "content": None,
            "tool_calls": [
                {
                    "id": "test-call",
                    "type": "function",
                    "function": {"name": "screen_risks", "arguments": "{}"},
                }
            ],
        }

    monkeypatch.setattr(workflow, "completion", fake)
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    runner = uvicorn.Server(uvicorn.Config(server.app, log_level="error"))
    thread = threading.Thread(
        target=runner.run, kwargs={"sockets": [sock]}, daemon=True
    )
    thread.start()
    try:
        for _ in range(100):
            if runner.started:
                break
            time.sleep(0.02)
        with sync_playwright() as p:
            browser = p.chromium.launch(
                executable_path=os.environ["FINGUARD_BROWSER"], headless=True
            )
            page = browser.new_page(viewport={"width": 1440, "height": 1000})
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(f"http://127.0.0.1:{port}")
            assert page.locator("html").get_attribute("lang") == "zh"
            page.locator("#lang").click()
            page.reload()
            assert page.locator("html").get_attribute("lang") == "en"
            page.locator("#token").fill("browser-test-token-" + "b" * 32)
            page.locator("#file").set_input_files(
                {
                    "name": "explicit-test-fixture.pdf",
                    "mimeType": "application/pdf",
                    "buffer": pdf_bytes(),
                }
            )
            page.locator("#consent").check()
            page.locator("#upload").click()
            expect(page.locator("#state")).to_have_text(
                "Needs confirmation", timeout=10000
            )
            for checkbox in page.locator(".selected").all():
                checkbox.check()
            page.locator("#confirm").click()
            expect(page.locator("#state")).to_have_text("Completed", timeout=10000)
            assert "0.8000" in page.locator("#results").inner_text()
            assert "LIQUIDITY" in page.locator("#results").inner_text()
            page.locator("#results button").filter(has_text="page:1").first.click()
            assert page.locator('[id="page:1"]').get_attribute("open") is not None
            with page.expect_download() as download:
                page.get_by_role("button", name="Download PDF").click()
            assert download.value.suggested_filename == "finguard-report.pdf"
            page.set_viewport_size({"width": 390, "height": 844})
            assert page.evaluate(
                "document.documentElement.scrollWidth <= window.innerWidth"
            )
            assert not errors
            browser.close()
    finally:
        runner.should_exit = True
        thread.join(timeout=5)
        sock.close()

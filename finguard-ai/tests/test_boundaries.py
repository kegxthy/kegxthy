import io
import zipfile
import httpx
import pytest
import workflow
from finance import Figure, calculate, screen
from test_workflow import fig


def test_unrounded_threshold():
    a, b = fig("current_assets", "99999"), fig("current_liabilities", "100000")
    r, _ = calculate([a, b])
    assert r["current_ratio"]["value"] == "1.0000"
    assert screen([a, b], r)[0]["code"] == "LIQUIDITY"


def test_precision_and_zip_budget():
    f = fig()
    f["value"] = "1e-100"
    with pytest.raises(ValueError):
        Figure.model_validate(f)
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("large", b"0" * (41 * 1024 * 1024))
    with pytest.raises(ValueError, match="Expanded"):
        workflow.extract(stream.getvalue(), "a.xlsx")


def test_large_finite_ratio():
    a, b = fig("current_assets", "1e20"), fig("current_liabilities", "0.000000000001")
    r, _ = calculate([a, b])
    assert r["current_ratio"]["value"] == "100000000000000000000000000000000.0000"


@pytest.mark.asyncio
async def test_transport_contract(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "test-only")
    monkeypatch.setenv("LLM_BASE_URL", "https://api.deepseek.com")

    def handler(request):
        import json

        data = json.loads(request.content)
        assert str(request.url) == "https://api.deepseek.com/chat/completions"
        assert data["tools"] == workflow.TOOLS and data["thinking"] == {
            "type": "disabled"
        }
        return httpx.Response(200, json={"choices": [{"message": {"content": "{}"}}]})

    original = httpx.AsyncClient
    monkeypatch.setattr(
        workflow.httpx,
        "AsyncClient",
        lambda **kw: original(transport=httpx.MockTransport(handler), **kw),
    )
    assert await workflow.completion([], workflow.TOOLS) == {"content": "{}"}
    monkeypatch.setenv("LLM_BASE_URL", "https://evil.example")
    with pytest.raises(ValueError, match="approved"):
        await workflow.completion([])

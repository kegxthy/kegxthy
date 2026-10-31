import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

TEST_TOKEN = "test-workspace-token-" + "a" * 32


@pytest.fixture(autouse=True)
def secure_workspace(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setenv("FINGUARD_ACCESS_TOKEN", TEST_TOKEN)
    monkeypatch.setenv("FINGUARD_MODE", "workspace")
    monkeypatch.setenv("FINGUARD_RETENTION_HOURS", "24")

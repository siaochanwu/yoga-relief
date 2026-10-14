from yoga_relief.config import Settings


def test_defaults(monkeypatch):
    monkeypatch.delenv("YOGA_MODEL", raising=False)
    monkeypatch.delenv("YOGA_LIVE_AI", raising=False)
    s = Settings(_env_file=None)
    assert s.claude_model == "claude-opus-5-5"
    assert s.live_ai is False


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("YOGA_MODEL", "claude-sonnet-5-5")
    monkeypatch.setenv("YOGA_LIVE_AI", "true")
    s = Settings(_env_file=None)
    assert s.claude_model == "claude-sonnet-5-5"
    assert s.live_ai is True

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


def test_env_file_with_empty_values_falls_back_to_defaults(tmp_path, monkeypatch):
    # .env.example 直接複製成 .env 的情境：值是空字串
    monkeypatch.delenv("YOGA_MODEL", raising=False)
    monkeypatch.delenv("YOGA_LIVE_AI", raising=False)
    env = tmp_path / ".env"
    env.write_text("ANTHROPIC_API_KEY=\nYOGA_MODEL=\nYOGA_LIVE_AI=\n", encoding="utf-8")
    s = Settings(_env_file=env)
    assert s.claude_model == "claude-opus-5-5"
    assert s.live_ai is False
    assert s.anthropic_api_key is None


def test_env_file_api_key_is_read(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    env = tmp_path / ".env"
    env.write_text("ANTHROPIC_API_KEY=sk-test-123\n", encoding="utf-8")
    assert Settings(_env_file=env).anthropic_api_key == "sk-test-123"

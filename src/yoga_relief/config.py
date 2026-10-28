"""環境變數設定（含 .env）。

pydantic-settings 讀 .env 只會填進這個物件，不會匯出到 os.environ，
所以 ANTHROPIC_API_KEY 也要在這裡宣告，再由程式明確傳給 SDK。
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # env_ignore_empty：把 .env.example 直接複製成 .env 時，空值要當作「沒設定」而不是空字串
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    claude_model: str = Field(default="claude-opus-5-5", validation_alias="YOGA_MODEL")
    live_ai: bool = Field(default=False, validation_alias="YOGA_LIVE_AI")
    anthropic_api_key: str | None = Field(default=None, validation_alias="ANTHROPIC_API_KEY")

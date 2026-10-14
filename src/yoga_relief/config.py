"""環境變數設定。SDK 自己讀 ANTHROPIC_API_KEY，這裡不重複宣告。"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    claude_model: str = Field(default="claude-opus-5-5", validation_alias="YOGA_MODEL")
    live_ai: bool = Field(default=False, validation_alias="YOGA_LIVE_AI")

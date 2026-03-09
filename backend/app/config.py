from pathlib import Path

from pydantic_settings import BaseSettings
from typing import Literal

# Resolve paths relative to the backend directory, not cwd
BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    database_url: str = f"sqlite:///{BACKEND_DIR / 'email_agent.db'}"

    gmail_credentials_path: str = "credentials.json"
    gmail_token_path: str = "token.json"

    followup_delay_1: int = 3
    followup_delay_2: int = 7
    followup_delay_3: int = 14

    email_connector: Literal["gmail", "mock"] = "mock"

    class Config:
        env_file = str(BACKEND_DIR / ".env")


settings = Settings()

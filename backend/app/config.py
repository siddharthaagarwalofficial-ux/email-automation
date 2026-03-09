from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    database_url: str = "sqlite:///./email_agent.db"

    gmail_credentials_path: str = "credentials.json"
    gmail_token_path: str = "token.json"

    followup_delay_1: int = 3
    followup_delay_2: int = 7
    followup_delay_3: int = 14

    email_connector: Literal["gmail", "mock"] = "mock"

    class Config:
        env_file = ".env"


settings = Settings()

# backend/app/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    DATABASE_URL: PostgresDsn
    POKEMONTCG_API_KEY: str | None = None

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

settings = Settings()
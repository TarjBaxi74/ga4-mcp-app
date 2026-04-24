from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    GA4_PROPERTY_ID: str = ""

    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "gemini-2.5-pro"

    CORS_ORIGINS: list[str] = Field(
        default=[
            "http://localhost:5173",
            "http://localhost:3000",
        ]
    )

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
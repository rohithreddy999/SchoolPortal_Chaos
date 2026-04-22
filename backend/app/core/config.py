from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    school_name: str = "Sri Satyam High School"
    app_name: str = "Sri Satyam High School Fee Portal"
    api_prefix: str = "/api"
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5433/school_portal"
    secret_key: str = "change-this-secret-key"
    access_token_expire_minutes: int = 720
    default_admin_username: str = "admin"
    default_admin_password: str = "admin123"
    backend_cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

import os

from dotenv import load_dotenv


load_dotenv(override=True)


class Settings:
    environment: str = os.environ.get("ENVIRONMENT", "development")
    secret_key: str = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    aadhaar_token_key: str = os.environ.get("AADHAAR_TOKEN_KEY", secret_key)
    algorithm: str = os.environ.get("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "720"))
    school_name: str = os.environ.get("SCHOOL_NAME", "School Fee Portal")
    redis_url: str = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    rate_limit_max_failures: int = int(os.environ.get("RATE_LIMIT_MAX_FAILURES", "5"))
    rate_limit_window_seconds: int = int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "300"))

    @property
    def using_insecure_secret(self) -> bool:
        return self.secret_key in {"", "change-me", "dev-secret-change-me"}

    @property
    def using_insecure_aadhaar_key(self) -> bool:
        return self.aadhaar_token_key in {"", "change-me", "dev-secret-change-me"}

    def validate_security(self) -> None:
        if self.environment.lower() not in {"prod", "production"}:
            return
        if self.using_insecure_secret:
            raise RuntimeError("SECRET_KEY must be set to a strong value in production")
        if self.using_insecure_aadhaar_key:
            raise RuntimeError("AADHAAR_TOKEN_KEY must be set to a strong value in production")


settings = Settings()


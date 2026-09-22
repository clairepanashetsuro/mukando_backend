from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Mukando API"
    environment: str = "development"

    # Development/test use the local database. Production uses the production URL.
    database_url: str = ""
    database_url_local: str = "postgresql+psycopg://postgres:postgres@localhost:5432/mukando_db"
    database_url_production: str = ""

    frontend_url: str = "http://localhost:3000"
    jwt_private_key: str = ""
    jwt_public_key: str = ""
    jwt_private_key_path: str = "keys/private.pem"
    jwt_public_key_path: str = "keys/public.pem"
    jwt_algorithm: str = "RS256"
    access_token_expire_minutes: int = 1440
    refresh_token_expire_minutes: int = 1440
    password_reset_expire_minutes: int = 30
    rate_limit: str = "100/minute"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@example.com"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @staticmethod
    def _sync_database_url(url: str) -> str:
        return url.replace("postgresql://", "postgresql+psycopg://", 1)

    @property
    def active_database_url(self) -> str:
        environment = self.environment.lower().strip()

        if environment == "production":
            if not self.database_url_production:
                # Backwards-compatible support for an existing production DATABASE_URL.
                if self.database_url:
                    return self.database_url
                raise RuntimeError(
                    "DATABASE_URL_PRODUCTION is required when ENVIRONMENT=production."
                )
            return self.database_url_production

        # Development/test must not accidentally connect to production.
        if environment == "test" and self.database_url:
            return self._sync_database_url(self.database_url)
        return self._sync_database_url(self.database_url_local)

    @staticmethod
    def _normalise_key(value: str) -> str:
        return value.replace("\\n", "\n")

    def _read_key_file(self, configured_path: str, label: str) -> str:
        path = Path(configured_path)
        if not path.is_absolute():
            path = BASE_DIR / path
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise RuntimeError(
                f"{label} not configured. Set the corresponding environment variable "
                f"or create the key file at {path}. See backend/README.md."
            ) from exc

    def private_key(self) -> str:
        if self.jwt_private_key:
            return self._normalise_key(self.jwt_private_key)
        return self._read_key_file(self.jwt_private_key_path, "JWT private key")

    def public_key(self) -> str:
        if self.jwt_public_key:
            return self._normalise_key(self.jwt_public_key)
        return self._read_key_file(self.jwt_public_key_path, "JWT public key")


settings = Settings()

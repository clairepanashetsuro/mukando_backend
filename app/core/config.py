
from pathlib import Path

import jwt
from cryptography.hazmat.primitives import serialization
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Mukando API"
    environment: str = "development"

    database_url: str = ""
    database_url_local: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/mukando"
    )
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

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    @property
    def active_database_url(self) -> str:
        environment = self.environment.lower().strip()

        if environment == "production":
            if not self.database_url_production:
                raise RuntimeError(
                    "DATABASE_URL_PRODUCTION is required "
                    "when ENVIRONMENT=production."
                )

            return self.database_url_production

        if environment == "test":
            if self.database_url:
                return self.database_url

            return self.database_url_local

        return self.database_url_local

    @staticmethod
    def _normalise_key(value: str) -> str:
        return value.replace("\\n", "\n").strip()

    def _read_key_file(self, configured_path: str, label: str) -> str:
        path = Path(configured_path)

        if not path.is_absolute():
            path = BASE_DIR / path

        try:
            return self._normalise_key(
                path.read_text(encoding="utf-8")
            )
        except FileNotFoundError as exc:
            raise RuntimeError(
                f"{label} not configured. Set the corresponding "
                f"environment variable or create the key file at {path}. "
                "See backend/README.md."
            ) from exc

    def private_key(self) -> str:
        if self.jwt_private_key:
            return self._normalise_key(self.jwt_private_key)

        return self._read_key_file(
            self.jwt_private_key_path,
            "JWT private key",
        )

    def public_key(self) -> str:
        if self.jwt_public_key:
            return self._normalise_key(self.jwt_public_key)

        return self._read_key_file(
            self.jwt_public_key_path,
            "JWT public key",
        )


settings = Settings()


def diagnose_jwt_configuration() -> None:
    try:
        if settings.jwt_algorithm != "RS256":
            print("JWT diagnostic: expected RS256.")

        private_key = settings.private_key()
        public_key = settings.public_key()

        private_obj = serialization.load_pem_private_key(
            private_key.encode(),
            password=None,
        )
        public_obj = serialization.load_pem_public_key(
            public_key.encode(),
        )

        keys_match = (
            private_obj.public_key().public_numbers()
            == public_obj.public_numbers()
        )

        print("JWT private key parses: OK")
        print("JWT public key parses: OK")
        print("JWT keys match:", keys_match)

        if not keys_match:
            return

        jwt.encode(
            {"sub": "diagnostic"},
            private_key,
            algorithm=settings.jwt_algorithm,
        )
        print("JWT signing test: OK")

    except Exception as exc:
        print(
            "JWT diagnostic failed:",
            type(exc).__name__,
            str(exc),
        )


if settings.environment.lower().strip() == "production":
    diagnose_jwt_configuration()

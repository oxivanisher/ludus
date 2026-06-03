from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    redis_url: str = "redis://localhost:6379"
    session_ttl_days: int = 30
    finished_session_ttl_days: int = 3

    # Web Push / VAPID — leave empty to disable push notifications.
    # Generate keys with: python -m core.vapid_gen
    vapid_private_key: str = ""
    vapid_public_key: str = ""
    vapid_contact_email: str = "admin@example.com"

    git_commit: str = "dev"

    # Abuse protection — cap total concurrent sessions and public open games.
    # With ~50 users each holding a few games, 200 total gives comfortable headroom.
    max_active_sessions: int = 200
    max_public_sessions: int = 20

    @property
    def session_ttl(self) -> int:
        return self.session_ttl_days * 86400

    @property
    def finished_session_ttl(self) -> int:
        return self.finished_session_ttl_days * 86400


settings = Settings()

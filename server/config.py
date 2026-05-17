import os
from functools import lru_cache

from dotenv import load_dotenv


load_dotenv()


class Settings:
    def __init__(self) -> None:
        self.okx_api_key = self._get_required("OKX_API_KEY")
        self.okx_secret_key = self._get_required("OKX_SECRET_KEY")
        self.okx_passphrase = self._get_required("OKX_PASSPHRASE")
        self.okx_base_url = os.getenv("OKX_BASE_URL", "https://www.okx.com").rstrip("/")
        self.okx_trade_mode = os.getenv("OKX_TRADE_MODE", "isolated")
        self.okx_default_size = os.getenv("OKX_DEFAULT_SIZE", "1")
        self.webhook_secret = os.getenv("WEBHOOK_SECRET", "")
        self.port = int(os.getenv("PORT", "8000"))
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.sqlite_path = os.getenv("SQLITE_PATH", "webhook.db")
        self.http_timeout_seconds = float(os.getenv("OKX_HTTP_TIMEOUT", "10"))
        self.duplicate_window_seconds = int(os.getenv("DUPLICATE_WINDOW_SECONDS", "5"))

    @staticmethod
    def _get_required(name: str) -> str:
        value = os.getenv(name, "").strip()
        if not value:
            raise RuntimeError(f"Missing required environment variable: {name}")
        return value


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

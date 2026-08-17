from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProviderMode(str, Enum):
    FREE = "free"
    PAID = "paid"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    provider_mode: ProviderMode = ProviderMode.FREE
    cache_dir: str = ".cache"
    anthropic_api_key: str = ""
    mapbox_access_token: str = ""
    openrouteservice_api_key: str = ""


settings = Settings()

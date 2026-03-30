from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    gemini_api_key: str = ""
    database_url: str = "sqlite+aiosqlite:///./data/gyg_scout.db"
    scraper_headless: bool = True
    scraper_timeout: int = 30000
    scraper_max_pages: int = 5
    scraper_delay_min: float = 2.0
    scraper_delay_max: float = 5.0

    model_config = {"env_file": ".env"}


settings = Settings()

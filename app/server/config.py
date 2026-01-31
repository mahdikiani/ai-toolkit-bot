"""FastAPI server configuration."""

import dataclasses
import os
from pathlib import Path

import dotenv
from fastapi_mongo_base.core import config

dotenv.load_dotenv()


@dataclasses.dataclass
class Settings(config.Settings):
    """Server config settings."""

    project_name: str = os.getenv("PROJECT_NAME", "pishrun ai")
    base_dir: Path = Path(__file__).resolve().parent.parent
    base_path: str = "/api/ai/v1"

    coverage_dir: Path = base_dir / "htmlcov"
    currency: str = "IRR"

    finance_api_key: str | None = os.getenv("API_KEY")
    ai_api_key: str | None = os.getenv("AI_API_KEY")
    media_api_key: str | None = os.getenv("MEDIA_API_KEY")

    ai_url: str = os.getenv("AI_BASE_URL")

    openrouter_api_key: str | None = os.getenv("OPENROUTER_API_KEY")
    openrouter_base_url: str = os.getenv(
        "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
    )
    soniox_api_key: str | None = os.getenv("SONIOX_API_KEY")

    @classmethod
    def get_log_config(cls, console_level: str = "INFO", **kwargs: object) -> dict:
        log_config = {
            "formatters": {
                "standard": {
                    "format": "[{levelname} {name} : {filename}:{lineno} : {asctime} -> {funcName:10}] {message}",  # noqa: E501
                    "style": "{",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": console_level,
                    "formatter": "standard",
                },
                "file": {
                    "class": "logging.FileHandler",
                    "level": "INFO",
                    "formatter": "standard",
                    "filename": "logs/app.log",
                },
            },
            "loggers": {
                "": {
                    "handlers": [
                        "console",
                        "file",
                    ],
                    "level": console_level,
                    "propagate": True,
                },
            },
            "version": 1,
        }
        return log_config

import logging
from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager, contextmanager
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

import httpx
from fastapi_mongo_base.schemas import UserOwnedEntitySchema
from fastapi_mongo_base.tasks import TaskMixin
from fastapi_mongo_base.utils import basic

from apps.bots.handlers import get_bot
from server.config import Settings

from .schemas import MessengerMetaDataSchema


class OCRSchema(UserOwnedEntitySchema, TaskMixin):
    file_url: str
    webhook_url: str
    meta_data: MessengerMetaDataSchema | dict | None = None
    result: str | None = None

    usage_amount: float | None = None
    usage_id: str | None = None
    task_type: str = "ocr"


class OCRClient:
    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        self.httpx_kwargs = {
            "base_url": Settings.ai_url,
            "headers": {"x-api-key": Settings.ai_api_key or ""},
            **kwargs,
        }

    @asynccontextmanager
    async def aclient(self) -> AsyncGenerator[httpx.AsyncClient]:
        async with httpx.AsyncClient(**self.httpx_kwargs) as client:
            yield client

    @contextmanager
    def client(self) -> Generator[httpx.Client]:
        with httpx.Client(**self.httpx_kwargs) as client:
            yield client

    @basic.try_except_wrapper
    async def aprocess_ocr_webhook(self, ocr_webhook: OCRSchema) -> None:
        logging.info("Processing OCR webhook: %s", ocr_webhook)
        file_name = Path(urlparse(ocr_webhook.file_url).path)

        async with self.aclient() as client:
            request = await client.get(f"/ocrs/{ocr_webhook.uid}/result")
            request.raise_for_status()

            file_content = BytesIO(request.content)
            file_content.name = f"{file_name.stem}.md"

            bot = get_bot(ocr_webhook.meta_data.bot_name)
            await bot.send_document(ocr_webhook.meta_data.chat_id, file_content)

    async def asubmit_ocr_task(self, file_url: str, meta_data: dict) -> OCRSchema:
        from apps.ai import routes

        async with self.aclient() as client:
            webhook_url = routes.router.url_path_for("ocr_webhook")
            request = await client.post(
                "/ocrs",
                json={
                    "file_url": file_url,
                    "meta_data": meta_data,
                    "webhook_url": f"https://{Settings.root_url}{Settings.base_path}/{webhook_url}",
                },
            )
            request.raise_for_status()
            response = OCRSchema.model_validate(request.json())
            return response

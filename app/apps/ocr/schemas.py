import base64
from io import BytesIO

import httpx
from fastapi_mongo_base.schemas import UserOwnedEntitySchema
from fastapi_mongo_base.tasks import TaskMixin
from pydantic import BaseModel


class OcrTaskSchemaCreate(BaseModel):
    file_url: str
    user_id: str | None = None

    @property
    def is_pdf(self) -> bool:
        return self.file_url.endswith(".pdf")

    async def file_content(self) -> BytesIO:
        if hasattr(self, "_file_content"):
            return self._file_content

        self._file_content = BytesIO()
        async with httpx.AsyncClient() as client:
            response = await client.get(self.file_url)
            self._file_content.write(response.content)
            self._file_content.seek(0)
            return self._file_content

    async def file_content_base64(self) -> str:
        content = await self.file_content()
        return base64.b64encode(content.getvalue()).decode("utf-8")


class OcrTaskSchema(UserOwnedEntitySchema, TaskMixin, OcrTaskSchemaCreate):
    result: str | None = None
    usage_amount: float | None = None
    usage_id: str | None = None

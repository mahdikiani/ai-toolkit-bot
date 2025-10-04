from typing import Self

from fastapi_mongo_base.models import UserOwnedEntity
from fastapi_mongo_base.tasks import TaskStatusEnum

from .schemas import OcrTaskSchema


class OcrTask(UserOwnedEntity, OcrTaskSchema):  # type: ignore[misc]
    async def start_processing(self) -> Self:
        from . import services

        self.task_status = TaskStatusEnum.processing
        return await services.process_ocr(self)  # type: ignore[return-value]

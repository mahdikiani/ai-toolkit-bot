from fastapi_mongo_base.models import UserOwnedEntity

from .schemas import OcrTaskSchema


class OcrTask(OcrTaskSchema, UserOwnedEntity):
    async def start_processing(self) -> None:
        from . import services

        self.task_status = "processing"
        return await services.process_ocr_task_service(self)

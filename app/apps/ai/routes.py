from fastapi import APIRouter, BackgroundTasks

from .ocr import OCRClient, OCRSchema

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/ocr/webhook/")
async def ocr_webhook(
    ocr_webhook: OCRSchema, background_tasks: BackgroundTasks
) -> None:
    background_tasks.add_task(OCRClient().aprocess_ocr_webhook, ocr_webhook)

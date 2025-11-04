from fastapi import APIRouter
from fastapi_mongo_base.core import app_factory

from apps.ai.routes import router as ai_router
from apps.bots.handlers import BotHandler
from apps.bots.routes import router as bots_router

from . import config

app = app_factory.create_app(
    settings=config.Settings(), init_functions=[BotHandler().setup]
)
server_router = APIRouter()

for router in [bots_router, ai_router]:
    server_router.include_router(router)

app.include_router(server_router, prefix=config.Settings.base_path)

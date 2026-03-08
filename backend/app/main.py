from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings
from app.core.db import SessionLocal, engine
from app.models.base import Base
from app import models  # noqa: F401
from app.services.mqtt_service import MQTTService
from app.services.tool_seed import seed_tools_if_empty
from app.services.user_seed import seed_users_if_empty

settings = get_settings()
mqtt_service = MQTTService()


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as session:
        await seed_tools_if_empty(session)
        await seed_users_if_empty(session)

    mqtt_service.start()
    yield
    mqtt_service.stop()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(router)

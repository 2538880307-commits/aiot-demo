from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routes import router
from app.core.config import get_settings
from app.core.db import SessionLocal, engine
from app.models.base import Base
from app import models  # noqa: F401
from app.services.mqtt_service import MQTTService
from app.services.system_seed import seed_system_configs
from app.services.tool_seed import seed_tools_if_empty
from app.services.user_seed import patch_default_user_passwords, seed_users_if_empty

settings = get_settings()
mqtt_service = MQTTService()


@asynccontextmanager
async def lifespan(_: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Backward-compatible column patch for existing databases.
        await conn.execute(text('ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(256)'))

    async with SessionLocal() as session:
        await seed_tools_if_empty(session)
        await seed_users_if_empty(session)
        await patch_default_user_passwords(session)
        await seed_system_configs(session)

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

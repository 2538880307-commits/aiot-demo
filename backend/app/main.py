from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import get_settings
from app.services.mqtt_service import MQTTService

settings = get_settings()
mqtt_service = MQTTService()


@asynccontextmanager
async def lifespan(_: FastAPI):
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

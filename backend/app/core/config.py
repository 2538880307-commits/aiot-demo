from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'AIoT Tool Monitoring API'
    app_env: str = 'dev'
    app_host: str = '0.0.0.0'
    app_port: int = 8000

    postgres_host: str = 'localhost'
    postgres_port: int = 5432
    postgres_db: str = 'aiot_monitor'
    postgres_user: str = 'aiot_user'
    postgres_password: str = 'aiot_password'

    redis_host: str = 'localhost'
    redis_port: int = 6379
    redis_password: str = ''

    mqtt_host: str = 'localhost'
    mqtt_port: int = 1883
    mqtt_username: str = ''
    mqtt_password: str = ''
    mqtt_topic_detect: str = 'rail/line1/siteA/detect'
    mqtt_topic_alert: str = 'rail/line1/siteA/alert'

    tool_count_model_path: str = '/app/model/best.pt'
    tool_count_conf: float = 0.25
    tool_count_iou: float = 0.45
    tool_count_max_image_mb: int = 10

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def redis_url(self) -> str:
        auth = f":{self.redis_password}@" if self.redis_password else ''
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/0"


@lru_cache
def get_settings() -> Settings:
    return Settings()

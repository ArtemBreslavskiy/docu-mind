from pydantic import BaseModel, Field
from src.configs.schemas.app.api import ApiConfig


class AppConfig(BaseModel):
    api: ApiConfig = Field(default_factory=ApiConfig)

from pydantic import BaseModel, Field
from src.config.schemas.app.api import ApiConfig
from src.config.schemas.app.models import ModelsConfig


class AppConfig(BaseModel):
    api: ApiConfig = Field(default_factory=ApiConfig)
    models: ModelsConfig = Field(default_factory=ModelsConfig)

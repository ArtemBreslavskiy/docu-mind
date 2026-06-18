from pydantic import BaseModel, Field
from typing import Union
from src.config.schemas.app.api import ApiConfig
from src.config.schemas.app.models import ModelsConfig
from src.config.schemas.app.storage import FAISSStorageConfig


class AppConfig(BaseModel):
    api: ApiConfig = Field(default_factory=ApiConfig)
    models: ModelsConfig = Field(default_factory=ModelsConfig)
    storage: Union[FAISSStorageConfig] = (Field(discriminator="type"))

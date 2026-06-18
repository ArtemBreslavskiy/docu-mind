from pydantic import BaseModel, Field


class ApiConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = Field(8000, ge=1024, le=65535)

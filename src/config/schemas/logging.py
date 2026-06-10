from pydantic import BaseModel, Field
from typing import Optional


class LoggerDefaultsConfig(BaseModel):
    name: str = "default"
    filename_pattern: str = "%Y%m%d_%H%M%S.log"
    use_colors: bool = True
    console: bool = True
    console_level: str = Field("INFO", pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    file: bool = True
    file_level: str = Field("DEBUG", pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    max_bytes: int = Field(10485_760, ge=1024, le=1073741824)  # 10MB  1KB  1GB
    backup_count: int = Field(5, ge=0, le=100)
    fmt: str = "[%(asctime)s.%(msecs)03d] - %(module)10s:%(lineno)-3d %(levelname)-7s - %(message)s"
    datefmt: str = "%Y-%m-%d %H:%M:%S"
    encoding: str = Field("utf-8", pattern=r"^(utf-8|ascii|cp1251|latin-1)$")


class LoggerOverrideConfig(BaseModel):
    name: Optional[str] = None
    filename_pattern: Optional[str] = None
    use_colors: Optional[bool] = None
    console: Optional[bool] = None
    console_level: Optional[str] = None
    file: Optional[bool] = None
    file_level: Optional[str] = None
    max_bytes: Optional[int] = None
    backup_count: Optional[int] = None
    fmt: Optional[str] = None
    datefmt: Optional[str] = None
    encoding: Optional[str] = None


class LoggingConfig(BaseModel):
    default: LoggerDefaultsConfig = Field(default_factory=LoggerDefaultsConfig)
    types: dict[str, LoggerOverrideConfig] = Field(default_factory=dict)

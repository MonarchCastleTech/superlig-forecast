"""Typed project configuration."""

from pathlib import Path
from typing import Self

import yaml
from pydantic import BaseModel, ConfigDict, Field


class CompetitionConfig(BaseModel):
    """A Turkish competition included in the data pyramid."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1)
    tier: int = Field(ge=0, le=4)
    name: str = Field(min_length=1)


class Settings(BaseModel):
    """Root configuration loaded from YAML."""

    model_config = ConfigDict(frozen=True)

    competitions: tuple[CompetitionConfig, ...]

    @classmethod
    def load(cls, path: Path) -> Self:
        """Load and validate settings from a UTF-8 YAML file."""

        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        return cls.model_validate(payload)


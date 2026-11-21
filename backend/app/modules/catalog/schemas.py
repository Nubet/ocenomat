from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Level(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    level: int = Field(ge=0, le=4)
    name: str
    description: str


class Indicator(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    description: str
    levels: list[Level] = Field(min_length=5, max_length=5)


class Criterion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    name: str
    indicators: list[Indicator] = Field(min_length=1)


class CatalogResponse(BaseModel):
    id: UUID
    version: str
    source_name: str
    source_sha256: str
    criteria: list[Criterion]

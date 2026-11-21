from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    assessment_id: UUID
    kind: Literal["attachment"]
    filename: str
    media_type: str
    size: int
    sha256: str
    author_id: UUID
    created_at: datetime


class DocumentUploadResponse(BaseModel):
    document: DocumentResponse
    assessment_revision: int

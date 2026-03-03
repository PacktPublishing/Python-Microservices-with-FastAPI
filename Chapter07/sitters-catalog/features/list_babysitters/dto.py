from typing import Annotated

from pydantic import BaseModel, Field


class BabysitterSearchFilters(BaseModel):
    city: str | None = None
    min_rate: Annotated[float | None, Field(ge=0)] = None
    max_rate: Annotated[float | None, Field(ge=0)] = None
    language: str | None = None
    min_experience: Annotated[int | None, Field(ge=0)] = None
    is_active: bool | None = True

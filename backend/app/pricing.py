import json
import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class Pricing(BaseModel):
    model_config = ConfigDict(extra="forbid")
    currency: str = Field(pattern="^USD$")
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    source: str = Field(min_length=1, max_length=500)
    input_per_million: float = Field(ge=0, le=10000)
    output_per_million: float = Field(ge=0, le=10000)
    assumptions: str = Field(max_length=1000)


def snapshot(model):
    path = os.getenv("PRICING_FILE")
    if not path:
        return None
    table = json.loads(Path(path).read_text())
    value = table.get(model)
    return Pricing.model_validate(value).model_dump() if value else None

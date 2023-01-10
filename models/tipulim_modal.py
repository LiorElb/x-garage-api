from bson import ObjectId
from pydantic import BaseModel, Field, validator

from models.base_update_model import BaseUpdateModel, MISSING
from models.pyobjectid import PyObjectId


class TipulModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(...)
    storage_types: list[str] | list[dict] | None = Field(default=None)
    kind: int | None = Field(default=MISSING)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "name": "טיפול",
                "storage_types": ["ברקסים", "toyota"],
                "kind": 0
            }
        }


class UpdateTipulModel(BaseUpdateModel):
    name: str = Field(default=MISSING)
    storage_types: list[dict] | None = Field(default=MISSING)
    kind: int | None = Field(default=MISSING)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "name": "טיפול",
                "storage_types": ["דגש", "ברקסים"],
                "kind": 0
            }
        }

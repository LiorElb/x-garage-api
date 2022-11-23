from bson import ObjectId
from pydantic import BaseModel, Field, validator

from models.base_update_model import BaseUpdateModel, MISSING
from models.pyobjectid import PyObjectId


class StorageCategoryModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(...)
    number: int | None = Field(default=None)
    sub_categories: list[str] | None = Field(default=None)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "name": "breksim",
                "number": "1",
                "sub_categories": ["honda", "toyota"],
            }
        }


class UpdateStorageCategoryModel(BaseUpdateModel):
    name: str | None = Field(default=MISSING)
    number: int | None = Field(default=MISSING)
    sub_categories: list[str] | None = Field(default=MISSING)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "name": "breksim",
                "number": "1",
                "sub_categories": ["honda", "toyota"],
            }
        }

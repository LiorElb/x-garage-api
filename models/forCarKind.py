from bson import ObjectId
from pydantic import BaseModel, Field, validator

from models.base_update_model import BaseUpdateModel, MISSING
from models.pyobjectid import PyObjectId


class CarKindModel(BaseModel):
    name: str = Field(...)
    degem: str = Field(...)
    shana: str = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True

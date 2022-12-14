from bson import ObjectId
from pydantic import BaseModel, Field, validator

from models.base_update_model import BaseUpdateModel, MISSING
from models.pyobjectid import PyObjectId


class AreaModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(...)
    number: int = Field(...)
    multi:  bool | None = Field(default=False)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "name": "lift big",
                "number": "1",
                "multi": "false",
            }
        }


class UpdateAreaModel(BaseUpdateModel):
    name: str | None = Field(default=MISSING)
    number: int | None = Field(default=MISSING)
    multi: bool | None = Field(default=MISSING)
    

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "name": "lift big",
                "number": "1",
                "multi": "false",
            }
        }

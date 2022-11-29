from bson import ObjectId
from pydantic import BaseModel, Field, validator

from models.base_update_model import BaseUpdateModel, MISSING
from models.pyobjectid import PyObjectId


class TypeModel(BaseModel):

    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    list: list[str] | None = Field(default=None)
    number1: int = Field(default=None)
    number2: int = Field(default=None)
    number3: int = Field(default=None)
    number4: int = Field(default=None)
    note1: str | None = Field(default=None)
    note2: str | None = Field(default=None)
    note3: str | None = Field(default=None)
    note4: str | None = Field(default=None)|

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        schema_extra = {
            "example": {
                "id": ["טויוטה", "cross", "2020"],
                "number1": 1,
                "number2": 1,
                "number3": 1,
                "number4": 1,
                "note1": "111111111",
                "note2": "111111111",
                "note3": "111111111",
                "note4": "111111111",
            }
        }


class UpdateTypeModel(BaseUpdateModel):
    number1: int = Field(default=MISSING)
    number2: int = Field(default=MISSING)
    number3: int = Field(default=MISSING)
    number4: int = Field(default=MISSING)
    note1: str | None = Field(default=MISSING)
    note2: str | None = Field(default=MISSING)
    note3: str | None = Field(default=MISSING)
    note4:  str | None = Field(default=MISSING)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "id": ["טויוטה", "cross", "2020"],
                "number1": 1,
                "number2": 1,
                "number3": 1,
                "number4": 1,
                "note1": "111111111",
                "note2": "111111111",
                "note3": "111111111",
                "note4": "111111111",
            }
        }

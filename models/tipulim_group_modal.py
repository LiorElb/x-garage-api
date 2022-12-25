from bson import ObjectId
from pydantic import BaseModel, Field, validator

from models.base_update_model import BaseUpdateModel, MISSING
from models.pyobjectid import PyObjectId


class TipulGroupModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(...)
    tipulim: list[str] | None = Field(default=None)
    check_list: list[str] | None = Field(default=None)
    price: float | str= Field(default=0, gt=0)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "name": "טיפול",
                "price": 0,
                "tipulim": ["ברקסים", "toyota"],
                "check_list": ["לבדוק שמן", "toyota"]
            }
        }


class UpdateTipulGroupModel(BaseUpdateModel):
    name: str = Field(default=MISSING)
    tipulim: list[str] | None = Field(default=MISSING)
    check_list: list[str] | None = Field(default=MISSING)
    price: float = Field(default=MISSING)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "name": "טיפול",
                "price": 0,
                "tipulim": ["דגש", "ברקסים"],
                "check_list": ["honda", "לבדוק שמן"]
            }
        }

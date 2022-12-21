from bson import ObjectId
from pydantic import BaseModel, Field, validator

from models.base_update_model import BaseUpdateModel, MISSING
from models.pyobjectid import PyObjectId


class UsedModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(...)
    category: str = Field(...)
    sub: str | list[str] | None = Field(default=None)
    notes: str | None = Field(default=None)
    amount_in_stock: int = Field(default=0, gt=0)
    price_cost: float = Field(default=0, gt=0)
    price_sell: float = Field(default=0, gt=0)
    car_types: list[str] | list[dict] | None = Field(default=None)
    location: str | None = Field(default=None)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "name": "hammer",
                "category": "mechanic",
                "notes": "very heavy",
                "amount_in_stock": 1,
                "car_types": ["honda", "toyota"],
                "location": "C424"
            }
        }


class UpdateUsedModel(BaseUpdateModel):
    name: str = Field(default=MISSING)
    category: str = Field(default=MISSING)
    sub: list[str] | str = Field(default=MISSING)
    notes: str | None = Field(default=MISSING)
    description: str | None = Field(default=MISSING)
    price_cost: float = Field(default=MISSING)
    price_sell: float = Field(default=MISSING)
    amount_in_stock:  int = Field(default=MISSING)
    car_types: list[str] | list[dict] | None = Field(default=MISSING)
    location: str | None = Field(default=MISSING)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "name": "hammer",
                "category": "mechanic",
                "notes": "very heavy",
                "amount_in_stock": 1,
                "car_types": ["honda", "toyota"],
                "location": "C424"
            }
        }

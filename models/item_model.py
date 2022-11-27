from bson import ObjectId
from pydantic import BaseModel, Field, validator

from models.base_update_model import BaseUpdateModel, MISSING
from models.pyobjectid import PyObjectId


class ItemModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    barcode: str | None = Field(default=None)
    name: str = Field(...)
    category: str = Field(...)
    sub: list[str] | str | None = Field(default=None)
    supplier: str | None = Field(default=None)
    notes: str | None = Field(default=None)
    amount_in_stock: int = Field(default=0, gt=0)
    max_amount_in_stock: int = Field(default=0, gt=0)
    car_types: list[str] | None = Field(default=None)
    location: str | None = Field(default=None) 
    price_cost: int = Field(default=0, gt=0)
    price_sell: int = Field(default=0, gt=0)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "barcode": "1111111",
                "name": "hammer",
                "category": "mechanic",
                "sub": ["honda", "toyota"],
                "supplier": "mechanic",
                "notes": "very heavy",
                "amount_in_stock": 1,
                "max_amount_in_stock": 1,
                "car_types": ["honda", "toyota"],
                "location": "C424",
                "price_cost": "100",
                "price_sell": "400"
            }
        }


class UpdateItemModel(BaseUpdateModel):
    barcode: str | None = Field(default=MISSING)
    name: str = Field(default=MISSING)
    category: str = Field(default=MISSING)
    sub: list[str] | str | None = Field(default=MISSING)
    supplier: str = Field(default=MISSING)
    notes: str | None = Field(default=MISSING)
    amount_in_stock: int = Field(default=MISSING)
    max_amount_in_stock: int = Field(default=MISSING)
    car_types: list[str] | None = Field(default=MISSING)
    location: str | None = Field(default=MISSING)   
    price_cost: int = Field(default=MISSING)
    price_sell: int = Field(default=MISSING)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "barcode": "1111111",
                "name": "hammer",
                "category": "mechanic",
                "sub": ["honda", "toyota"],
                "supplier": "mechanic",
                "notes": "very heavy",
                "amount_in_stock": 1,
                "max_amount_in_stock": 1,
                "car_types": ["honda", "toyota"],
                "location": "C424",
                "price_cost": "100",
                "price_sell": "400"
            }
        }

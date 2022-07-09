from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field, EmailStr

from pyobjectid import PyObjectId

MISSING = set("__MISSING__")


class CustomerModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    cars: list[str] = Field(default_factory=list)
    name: str = Field(...)
    email: Optional[EmailStr] = Field(...)
    phone_number: str = Field(...)
    address: Optional[str] = Field(default=None)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "cars": ["123-12-123", "12-123-12"],
                "name": "John Doe",
                "email": "jdoe@example.com",
                "phone_number": "054-3532312",
                "address": "הדולב 4, גבעון החדשה",
            }
        }


class UpdateCustomerModel(BaseModel):
    cars: list[str] = Field(default=MISSING)
    name: str = Field(default=MISSING)
    email: Optional[EmailStr] = Field(default=MISSING)
    phone_number: str = Field(default=MISSING)
    address: Optional[str] = Field(default=MISSING)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "cars": ["123-12-123", "12-123-12"],
                "name": "John Doe",
                "email": "jdoe@example.com",
                "phone_number": "054-3532312",
                "address": "הדולב 4, גבעון החדשה",
            }
        }

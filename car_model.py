from bson import ObjectId
from pydantic import BaseModel, Field, EmailStr

from base_update_model import BaseUpdateModel, MISSING
from pyobjectid import PyObjectId


class CarModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    license_plate_number: str = Field(...)
    code: str | None = Field(default=None)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "jdoe@example.com",
                "phone_number": "054-3532312",
                "address": "123 Street, NYC",
            }
        }


class UpdateCarModel(BaseUpdateModel):
    license_plate_number: str | None = Field(default=MISSING)
    code: str | None = Field(default=MISSING)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "jdoe@example.com",
                "phone_number": "054-3532312",
                "address": "123 Street, NYC",
            }
        }

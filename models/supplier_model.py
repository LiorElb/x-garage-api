from bson import ObjectId
from pydantic import BaseModel, Field, validator

from models.base_update_model import BaseUpdateModel, MISSING
from models.pyobjectid import PyObjectId


class SupplierModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(...)
    phone_number: str | None = Field(default=None)
    email: str | None = Field(default=None)
    address: str | None = Field(default=None)
    note: str | None = Field(default=None)
    payment: str | None = Field(default=None)
    phone_book: list[dict] | None = Field(default=None)
    storage_types: list[str] | list[dict] | None = Field(default=None)

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
                "note": "screeming bitch",
                "phone_book": {"name": "cfasdf", "phone": "876543"},
                "payment":"payment",
                "storage_types": ["ברקסים", "toyota"],
            }
        }


class UpdateSupplierModel(BaseUpdateModel):
    name: str | None = Field(default=MISSING)
    phone_number: str | None = Field(default=MISSING)
    email: str | None = Field(default=MISSING)
    address: str | None = Field(default=MISSING)
    note: str | None = Field(default=MISSING)
    payment: str | None = Field(default=MISSING)
    phone_book: list[dict] | None = Field(default=MISSING)
    storage_types: list[str] | list[dict] | None = Field(default=MISSING)

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
                "note": "screeming bitch",
                "phone_book": {"name":"cfasdf","phone":"876543"},
                "payment":"payment",
                "storage_types": ["ברקסים", "toyota"],
            }
        }

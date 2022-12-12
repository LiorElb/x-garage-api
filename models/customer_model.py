from bson import ObjectId
from pydantic import BaseModel, Field

from models.base_update_model import BaseUpdateModel, MISSING
from models.pyobjectid import PyObjectId


class CustomerModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    cars: list[str] = Field(default_factory=list)
    name: str = Field(...)
    phone_number: str | None = Field(default=None)
    email: str | None = Field(default=None)
    address: str | None = Field(default=None)
    note: str | None = Field(default=None)
    phone_book: list[dict] | None = Field(default=None)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "cars": ["12312123", "1212312"],
                "name": "John Doe",
                "email": "jdoe@example.com",
                "phone_number": "054-3532312",
                "address": "123 Street, NYC",
                "note": "screeming bitch",
                "phone_book": {"name":"cfasdf","phone":"876543"}
            }
        }


class UpdateCustomerModel(BaseUpdateModel):
    cars: list[str] | None = Field(default=MISSING)
    name: str | None = Field(default=MISSING)
    phone_number: str | None = Field(default=MISSING)
    email: str | None = Field(default=MISSING)
    address: str | None = Field(default=MISSING)
    note: str | None = Field(default=MISSING)
    phone_book: list[dict] | None = Field(default=MISSING)

    class Config:
        arbitrary_types_allowed = True

        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "cars": ["12312123", "1212312"],
                "name": "John Doe",
                "email": "jdoe@example.com",
                "phone_number": "054-3532312",
                "address": "123 Street, NYC",
                "note": "screeming bitch",
                "phone_book": {"name":"cfasdf","phone":"876543"}
            }
        }

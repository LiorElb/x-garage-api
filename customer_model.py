from bson import ObjectId
from pydantic import BaseModel, Field, EmailStr, root_validator

from pyobjectid import PyObjectId


class CustomerModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    cars: list[str] = Field(default_factory=list)
    name: str = Field(...)
    phone_number: str = Field(...)
    email: EmailStr | None = Field(default=None)
    address: str | None = Field(default=None)

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
                "address": "123 Street, NYC",
            }
        }


class UpdateCustomerModel(BaseModel):
    _MISSING = object()

    cars: list[str] = Field(default=_MISSING)
    name: str = Field(default=_MISSING)
    phone_number: str = Field(default=_MISSING)
    email: EmailStr | None = Field(default=_MISSING)
    address: str | None = Field(default=_MISSING)

    @root_validator(pre=True)
    def not_empty(cls, values):
        if not any(v != cls._MISSING for v in values):
            raise ValueError('Must have at least 1 value')
        return values

    def dict(self, *args, **kwargs):
        kwargs['exclude_unset'] = True
        return super().dict(*args, **kwargs)

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
                "address": "123 Street, NYC",
            }
        }

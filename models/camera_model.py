from bson import ObjectId
from pydantic import BaseModel, Field, validator

from models.base_update_model import BaseUpdateModel, MISSING
from models.pyobjectid import PyObjectId


class CameraModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    license_plate_number: str = Field(...)
    time_stamp: str = Field(...)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "license_plate_number": "12312123",
                "time_stamp": "23456789"
            }
        }


class UpdateCameraModel(BaseUpdateModel):
    license_plate_number: str = Field(default=MISSING)
    time_stamp: str = Field(default=MISSING)
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "license_plate_number": "12312123",
                "time_stamp": "23456789"
            }
        }

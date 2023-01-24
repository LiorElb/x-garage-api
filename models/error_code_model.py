from bson import ObjectId
from pydantic import BaseModel, Field
from models.base_update_model import BaseUpdateModel, MISSING
from models.pyobjectid import PyObjectId


class ErrorCodeModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    error_code: str = Field(...)
    result: dict = Field(...)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "error_code": "12312123",
                "result": "dict",
            }
        }

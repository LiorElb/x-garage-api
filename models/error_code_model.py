from bson import ObjectId
from pydantic import BaseModel, Field
from models.base_update_model import BaseUpdateModel, MISSING
from models.pyobjectid import PyObjectId


class ErrorCodeModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    code: str = Field(...)
    definition: str = Field(...)
    cause: list[str] | None = Field(default=MISSING)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "code": "12312123",
                "definition": "dict",
                "cause": "definition,definition",
            }
        }

    def __init__(self, code: str, definition: str, cause: list[str] = None, **kwargs):
        self.code = code.lower()
        self.definition = definition
        self.cause = cause
        super().__init__(**kwargs)

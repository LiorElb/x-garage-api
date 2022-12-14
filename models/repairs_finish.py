from bson import ObjectId
from pydantic import BaseModel, Field
from models.base_update_model import BaseUpdateModel, MISSING
from models.pyobjectid import PyObjectId


class RepairFinishModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    license_plate_number: str = Field(...)
    area: dict = Field(...)
    tipul:list[dict] | None = Field(default=None)
    time_stamp_start: str | None = Field(default=None)
    time_stamp_end: str | None = Field(default=None)
    note: str | None = Field(default=None)
    rows: list[dict] | None = Field(default=None)
    products: list[dict] | None = Field(default=None)
    car: dict | None = Field(default=None)
    customer: dict | None = Field(default=None)
    total: float | None = Field(default=0)
    kilometer: int | None = Field(default=0)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "license_plate_number": ["12312123", "1212312"],
                "area": "John Doe",
                "tipul": "jdoe@example.com",
                "time_stamp_start": "054-3532312",
                "note": "screeming bitch",
                "rows": "screeming bitch",
                "products": "screeming bitch",
                "kilometer":"1234567",
                "car":"1234567",
            }
        }

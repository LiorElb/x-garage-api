from bson import ObjectId
from pydantic import BaseModel, Field
from models.base_update_model import BaseUpdateModel, MISSING
from models.pyobjectid import PyObjectId


class RepairModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    license_plate_number: str = Field(...)
    area_id: str = Field(...)
    tipul:list[dict] | None = Field(default=None)
    time_stamp_start: str | None = Field(default=None)
    note: str | None = Field(default=None)
    rows: list[dict] | None = Field(default=None)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "license_plate_number": ["12312123", "1212312"],
                "area_id": "John Doe",
                "tipul": "jdoe@example.com",
                "time_stamp_start": "054-3532312",
                "note": "screeming bitch",
                "rows": "screeming bitch",
            }
        }


class UpdateRepairModel(BaseUpdateModel):
    tipul: list[dict] = Field(default=MISSING)
    area_id: str = Field(default=MISSING)
    time_stamp_end: str | None = Field(default=MISSING)
    note: str | None = Field(default=MISSING)
    rows: list[dict] | None = Field(default=MISSING)

    class Config:
        arbitrary_types_allowed = True

        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "area_id": "John Doe",
                "tipul": "jdoe@example.com",
                "time_stamp_start": "054-3532312",
                "note": "screeming bitch",
                "rows": "screeming bitch",
            }
        }

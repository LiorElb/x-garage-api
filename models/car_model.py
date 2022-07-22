from bson import ObjectId
from pydantic import BaseModel, Field, EmailStr

from base_update_model import BaseUpdateModel, MISSING
from pyobjectid import PyObjectId


class CarModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    license_plate_number: str = Field(...)
    code: str | None = Field(default=None)
    tozeret_nm: str | None = Field(default=None)  # יצרן
    shnat_yitzur: int | None = Field(default=None)  # 2010
    degem_manoa: str | None = Field(default=None)  # "665 וברוט"
    tokef_dt: str | None = Field(default=None)  # 2023-06-21T00:00:00
    baalut: str | None = Field(default=None)  # "פרטי"
    misgeret: str | None = Field(default=None)  # "KPTN0B1FSAP059254"
    tzeva_rechev: str | None = Field(default=None)  # "אפור"
    zmig_kidmi: str | None = Field(default=None)  # "215/65R16"
    zmig_ahori: str | None = Field(default=None)  # "215/65R16"
    sug_delek_nm: str | None = Field(default=None)  # "דיזל"
    kinuy_mishari: str | None = Field(default=None)  # "RODIUS"

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
                "mispar_rechev": 2117772,
                "tozeret_nm": "סאנגיונג ד.קור",
                "shnat_yitzur": 2010,
                "degem_manoa": "665 וברוט",
                "tokef_dt": "2023-06-21T00:00:00",
                "baalut": "פרטי",
                "misgeret": "KPTN0B1FSAP059254",
                "tzeva_rechev": "אפור",
                "zmig_kidmi": "215/65R16",
                "zmig_ahori": "215/65R16",
                "sug_delek_nm": "דיזל",
                "kinuy_mishari": "RODIUS",
            }
        }

from bson import ObjectId
from pydantic import BaseModel, Field, validator

from models.base_update_model import BaseUpdateModel, MISSING
from models.pyobjectid import PyObjectId


class CarModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    license_plate_number: str = Field(...)
    code: str | None = Field(default=None)
    tozeret_nm: str | None = Field(default=None)
    shnat_yitzur: int | None = Field(default=None)
    degem_manoa: str | None = Field(default=None)
    tokef_dt: str | None = Field(default=None)
    baalut: str | None = Field(default=None)
    misgeret: str | None = Field(default=None)
    tzeva_rechev: str | None = Field(default=None)
    zmig_kidmi: str | None = Field(default=None)
    zmig_ahori: str | None = Field(default=None)
    sug_delek_nm: str | None = Field(default=None)
    kinuy_mishari: str | None = Field(default=None)

    @validator('license_plate_number')
    def digits_only(cls, v: str):
        if not v.isdigit():
            raise ValueError('license plate number must be a number')
        return v.title()

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
        schema_extra = {
            "example": {
                "license_plate_number": "1111111",
                "code": "*1234",
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
                "license_plate_number": "11-111-11",
                "code": "*3234",
            }
        }

        @validator('license_plate_number')
        def digits_only(cls, v: str):
            if not v.isdigit():
                raise ValueError('license plate number must be a number')
            return v.title()

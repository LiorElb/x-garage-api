from typing import List

from bson import ObjectId
from pydantic import BaseModel


class Customer(BaseModel):
    _id: ObjectId
    license_plate_numbers: List[str]
    name: str



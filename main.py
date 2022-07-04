import os
from http import HTTPStatus
from typing import List, Iterable

from fastapi import FastAPI, Response, HTTPException
import motor.motor_asyncio as motor

from customer import Customer

app = FastAPI()
MONGO_HOST = os.getenv('GARAGE_MONGO_HOST', 'localhost:27017/')
client = motor.AsyncIOMotorClient(f'mongodb://{MONGO_HOST}')
CUSTOMERS = client['main']['customers']


@app.get("/customers")
async def get_customers():
    return await CUSTOMERS.find(projection={"_id": 0}).to_list(length=None)


@app.post("/customers")
async def add_customer(customer: Customer):
    await assert_license_numbers_dont_already_exist(customer.license_plate_numbers)

    await CUSTOMERS.insert_one(customer.dict())
    return {"message": "success"}


@app.get("/customers/{license_plate_number}")
async def get_customer(license_plate_number: str):
    return await CUSTOMERS.find_one({"license_plate_numbers": license_plate_number}, projection={"_id": 0})


@app.put("/customers/{license_plate_number}")
async def update_customer(license_plate_number: str, customer: Customer):
    existing = await CUSTOMERS.find_one({"license_plate_numbers": license_plate_number})
    await assert_license_numbers_dont_already_exist(customer.license_plate_numbers,
                                                    allow=existing['license_plate_numbers'])

    await CUSTOMERS.replace_one({"license_plate_numbers": license_plate_number}, customer.dict())
    return {"message": "success"}


@app.delete("/customers/{license_plate_number}")
async def delete_customer(license_plate_number: str):
    result = await CUSTOMERS.delete_one({"license_plate_numbers": license_plate_number})
    return {'message': f'deleted {result.deleted_count} customers'}


@app.get("/customers/{license_plate_number}/cars/")
async def get_cars(license_plate_number: str):
    return await CUSTOMERS.find_one(
        {"license_plate_numbers": license_plate_number},
        projection={"_id": 0, "license_plate_numbers": 1}
    )['license_plate_numbers']


@app.post("/customers/{license_plate_number}/cars/{plate_number_to_add}")
async def add_car(license_plate_number: str, plate_number_to_add: str):
    await CUSTOMERS.update_one(
        {"license_plate_numbers": license_plate_number},
        update={"$push": {"license_plate_numbers": plate_number_to_add}}
    )
    return {"message": "success"}


@app.delete("/customers/{license_plate_number}/cars/{plate_number_to_delete}")
async def remove_car(license_plate_number: str, plate_number_to_delete: str):
    await CUSTOMERS.update_one(
        {"license_plate_numbers": license_plate_number},
        update={"$pull": {"license_plate_numbers": plate_number_to_delete}}
    )
    return {"message": "success"}


async def assert_license_numbers_dont_already_exist(license_plate_numbers: List[str], allow: Iterable[str] = ()):
    existing = await CUSTOMERS.find_one({"license_plate_numbers": {"$in": license_plate_numbers}})

    if existing is None:
        return

    if any(plate_num in existing['license_plate_numbers'] for plate_num in allow):
        return

    raise HTTPException(status_code=HTTPStatus.CONFLICT, detail="license number already exists")

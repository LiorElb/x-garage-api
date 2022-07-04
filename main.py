import os
from http import HTTPStatus

from fastapi import FastAPI, Response
from pymongo import MongoClient

from customer import Customer

app = FastAPI()
MONGO_HOST = os.getenv('GARAGE_MONGO_HOST', 'localhost:27017/')
client = MongoClient(f'mongodb://{MONGO_HOST}')
CUSTOMERS_COLLECTION = client['main']['customers']


@app.get("/customers")
async def get_customers():
    return list(CUSTOMERS_COLLECTION.find(projection={"_id": 0}))


@app.post("/customers")
async def add_customer(customer: Customer, response: Response):
    if CUSTOMERS_COLLECTION.find_one({"license_plate_numbers": {"$in": customer.license_plate_numbers}}) is not None:
        response.status_code = HTTPStatus.CONFLICT
        return {"message": "error - license number already exists"}

    CUSTOMERS_COLLECTION.insert_one(customer.dict())
    return {"message": "success"}


@app.get("/customers/{license_plate_number}")
async def get_customer(license_plate_number: str):
    return CUSTOMERS_COLLECTION.find_one({"license_plate_numbers": license_plate_number}, projection={"_id": 0})


@app.put("/customers/{license_plate_number}")
async def update_customer(license_plate_number: str, customer: Customer):
    CUSTOMERS_COLLECTION.replace_one({"license_plate_numbers": license_plate_number}, customer.dict())
    return {"message": "success"}


@app.delete("/customers/{license_plate_number}")
async def delete_customer(license_plate_number: str):
    result = CUSTOMERS_COLLECTION.delete_one({"license_plate_numbers": license_plate_number})
    return {'message': f'deleted {result.deleted_count} customers'}


@app.get("/customers/{license_plate_number}/cars/")
async def get_cars(license_plate_number: str):
    return CUSTOMERS_COLLECTION.find_one(
        {"license_plate_numbers": license_plate_number},
        projection={"_id": 0, "license_plate_numbers": 1}
    )['license_plate_numbers']


@app.post("/customers/{license_plate_number}/cars/{plate_number_to_add}")
async def add_car(license_plate_number: str, plate_number_to_add: str):
    CUSTOMERS_COLLECTION.update_one(
        {"license_plate_numbers": license_plate_number},
        update={"$push": {"license_plate_numbers": plate_number_to_add}}
    )
    return {"message": "success"}


@app.delete("/customers/{license_plate_number}/cars/{plate_number_to_delete}")
async def remove_car(license_plate_number: str, plate_number_to_delete: str):
    CUSTOMERS_COLLECTION.update_one(
        {"license_plate_numbers": license_plate_number},
        update={"$pull": {"license_plate_numbers": plate_number_to_delete}}
    )
    return {"message": "success"}

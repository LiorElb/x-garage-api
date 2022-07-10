from http import HTTPStatus

from fastapi import FastAPI, HTTPException, Body
from fastapi.encoders import jsonable_encoder

from models.customer_model import CustomerModel, UpdateCustomerModel
from mongo_client import CUSTOMERS

app = FastAPI()


@app.get("/customers", response_model=list[CustomerModel])
async def get_customers():
    return await CUSTOMERS.find().to_list(length=None)


@app.post("/customers", response_model=CustomerModel, status_code=HTTPStatus.CREATED)
async def add_customer(customer: CustomerModel):
    await assert_cars_dont_already_exist(customer.cars)

    customer = jsonable_encoder(customer)
    new_customer = await CUSTOMERS.insert_one(customer)
    return await CUSTOMERS.find_one({"_id": new_customer.inserted_id})


@app.get("/customers/{customer_id}", response_model=CustomerModel)
async def show_customer(customer_id: str):
    customer = await CUSTOMERS.find_one({"_id": customer_id})

    if customer is None:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    return customer


@app.put("/customers/{customer_id}", response_model=CustomerModel)
async def update_customer(customer_id: str, customer: UpdateCustomerModel = Body(...)):
    customer = customer.dict()
    existing = await CUSTOMERS.find_one({"_id": customer_id}, projection={"_id": 1})
    if existing is None:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    if 'cars' in customer:
        await assert_cars_dont_already_exist(customer['cars'], existing['_id'])

    await CUSTOMERS.update_one({"_id": customer_id}, {"$set": customer})

    return await CUSTOMERS.find_one({"_id": customer_id})


@app.delete("/customers/{customer_id}")
async def delete_customer(customer_id: str):
    result = await CUSTOMERS.delete_one({"_id": customer_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="No such customer")


@app.get("/customers/{customer_id}/cars/", response_model=list[str])
async def get_cars(customer_id: str):
    return await get_cars_by_id(customer_id)


@app.post("/customers/{customer_id}/cars/{plate_number_to_add}", response_model=list[str])
async def add_car(customer_id: str, plate_number_to_add: str):
    result = await CUSTOMERS.update_one(
        {"_id": customer_id},
        update={"$addToSet": {"cars": plate_number_to_add}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail='Car already exists')

    return await get_cars_by_id(customer_id)


@app.delete("/customers/{customer_id}/cars/{plate_number_to_delete}")
async def remove_car(customer_id: str, plate_number_to_delete: str):
    result = await CUSTOMERS.update_one(
        {"_id": customer_id},
        update={"$pull": {"cars": plate_number_to_delete}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='No such car')

    return await get_cars_by_id(customer_id)


async def assert_cars_dont_already_exist(license_plate_numbers: list[str], allowed_id: str = None) -> None:
    existing = await CUSTOMERS.find_one(
        {"cars": {"$in": license_plate_numbers},
         "_id": {"$ne": allowed_id}}
    )

    if existing is None:
        return

    raise HTTPException(status_code=HTTPStatus.CONFLICT, detail="license number already exists")


async def get_cars_by_id(customer_id) -> list[str]:
    customer = await CUSTOMERS.find_one({"_id": customer_id})
    try:
        return customer['cars']
    except TypeError:  # NoneType
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="No such customer")

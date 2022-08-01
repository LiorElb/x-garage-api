from http import HTTPStatus

from fastapi import FastAPI, HTTPException, Body
from fastapi.encoders import jsonable_encoder

from models.car_model import CarModel, UpdateCarModel
from models.customer_model import CustomerModel, UpdateCustomerModel
from app.mongo_client import CUSTOMERS, CARS

app = FastAPI()


# /customers

@app.get("/customers", response_model=list[CustomerModel], tags=['customers'])
async def get_customers():
    return await CUSTOMERS.find().to_list(length=None)


@app.post("/customers", response_model=CustomerModel, status_code=HTTPStatus.CREATED, tags=['customers'])
async def add_customer(customer: CustomerModel):
    await assert_cars_dont_belong_to_another_customer(customer.cars)

    customer = jsonable_encoder(customer)
    new_customer = await CUSTOMERS.insert_one(customer)
    return await CUSTOMERS.find_one({"_id": new_customer.inserted_id})


@app.get("/customers/{customer_id}", response_model=CustomerModel, tags=['customers'])
async def show_customer(customer_id: str):
    customer = await CUSTOMERS.find_one({"_id": customer_id})

    if customer is None:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")

    return customer


@app.put("/customers/{customer_id}", response_model=CustomerModel, tags=['customers'])
async def update_customer(customer_id: str, customer: UpdateCustomerModel = Body(...)):
    new_customer = customer.dict()

    existing = await CUSTOMERS.find_one({"_id": customer_id}, projection={"_id": 1})
    if existing is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"Customer {customer_id} not found")

    if 'cars' in new_customer:
        await assert_cars_dont_belong_to_another_customer(new_customer['cars'], existing['_id'])

    await CUSTOMERS.update_one({"_id": customer_id}, {"$set": new_customer})

    return await CUSTOMERS.find_one({"_id": customer_id})


@app.delete("/customers/{customer_id}", tags=['customers'])
async def delete_customer(customer_id: str):
    result = await CUSTOMERS.delete_one({"_id": customer_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="No such customer")


@app.get("/customers/{customer_id}/cars/", response_model=list[str], tags=['customers'])
async def get_cars_for_customer(customer_id: str):
    return await get_cars_by_id(customer_id)


@app.post("/customers/{customer_id}/cars/{plate_number_to_add}", response_model=list[str], tags=['customers'])
async def add_car_to_customer(customer_id: str, plate_number_to_add: str):
    result = await CUSTOMERS.update_one(
        {"_id": customer_id},
        update={"$addToSet": {"cars": plate_number_to_add}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail='Car already exists')

    return await get_cars_by_id(customer_id)


@app.delete("/customers/{customer_id}/cars/{plate_number_to_delete}", tags=['customers'])
async def remove_car_for_customer(customer_id: str, plate_number_to_delete: str):
    result = await CUSTOMERS.update_one(
        {"_id": customer_id},
        update={"$pull": {"cars": plate_number_to_delete}}
    )

    if result.modified_count == 0:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='No such car')

    return await get_cars_by_id(customer_id)


async def assert_cars_dont_belong_to_another_customer(license_plate_numbers: list[str], allowed_id: str = None) -> None:
    existing = await CUSTOMERS.find_one(
        {"cars": {"$in": license_plate_numbers},
         "_id": {"$ne": allowed_id}}
    )

    if existing is not None:
        raise HTTPException(status_code=HTTPStatus.CONFLICT, detail="license number already exists")


async def get_cars_by_id(customer_id) -> list[str]:
    customer = await CUSTOMERS.find_one({"_id": customer_id})
    try:
        return customer['cars']
    except TypeError:  # NoneType
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="No such customer")


# /cars

@app.get("/cars", response_model=list[CarModel], tags=['cars'])
async def get_cars():
    return await CARS.find().to_list(length=None)


@app.post("/cars", response_model=CarModel, status_code=HTTPStatus.CREATED, tags=['cars'])
async def add_car(car: CarModel):
    car = jsonable_encoder(car)
    new = await CARS.insert_one(car)
    return await CARS.find_one({"_id": new.inserted_id})


@app.get("/cars/{license_plate_number}", response_model=CarModel, tags=['cars'])
async def show_car(license_plate_number: str):
    car = await CARS.find_one({"license_plate_number": license_plate_number})

    if car is None:
        raise HTTPException(status_code=404, detail=f"Car {license_plate_number} not found")

    return car


@app.put("/cars/{license_plate_number}", response_model=CarModel, tags=['cars'])
async def update_car(license_plate_number: str, car: UpdateCarModel = Body(...)):
    new_car = car.dict()

    existing = await CARS.find_one(
        {"license_plate_number": license_plate_number},
        projection={"_id": 0, "license_plate_number": 1}
    )
    if existing is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"Car {license_plate_number} not found")

    await CARS.update_one({"license_plate_number": license_plate_number}, {"$set": new_car})

    return await CARS.find_one({"license_plate_number": license_plate_number})


@app.delete("/cars/{license_plate_number}", tags=['cars'])
async def delete_car(license_plate_number: str):
    result = await CARS.delete_one({"license_plate_number": license_plate_number})

    if result.deleted_count == 0:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="No such car")

    if result.deleted_count != 1:
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Deleted more than one car!")

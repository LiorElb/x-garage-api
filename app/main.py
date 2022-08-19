from http import HTTPStatus

import aiohttp
from fastapi import FastAPI, HTTPException, Body, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware

from models.car_model import CarModel, UpdateCarModel
from models.customer_model import CustomerModel, UpdateCustomerModel
from app.mongo_client import CUSTOMERS, CARS, ITEMS
from models.item_model import ItemModel, UpdateItemModel

app = FastAPI(version="0.4.2")

origins = [
    "*"  # TODO: Authentication - make sure its safe with chosen auth method
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


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


@app.get("/cars/types", response_model=list[str | None], tags=['cars'])
async def get_car_types():
    return await CARS.distinct("government_data.tozeret_nm")


@app.post("/cars", response_model=CarModel, status_code=HTTPStatus.CREATED, tags=['cars'])
async def add_car(car: CarModel, bg_tasks: BackgroundTasks):
    car = jsonable_encoder(car)
    new = await CARS.insert_one(car)
    new_car = await CARS.find_one(
        {"_id": new.inserted_id},
        projection={"license_plate_number": 1}
    )
    bg_tasks.add_task(enrich_car, new.inserted_id, new_car['license_plate_number'])
    return new_car


async def enrich_car(car_oid: str, license_plate_number: str):
    result = await get_car_info_from_gov_db(license_plate_number)
    await CARS.update_one({"_id": car_oid}, {"$set": {"government_data": result}})


async def get_car_info_from_gov_db(license_plate_number: str):
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        async with session.post(
                url='https://data.gov.il/api/3/action/datastore_search',
                json={
                    "resource_id": "053cea08-09bc-40ec-8f7a-156f0677aff3",
                    "filters": {
                        "mispar_rechev": [license_plate_number]
                    },
                    "limit": 2,
                    "offset": 0
                }
        ) as response:
            records = (await response.json())['result']['records']
            try:
                result = records[0]
                async with session.post(
                        url='https://data.gov.il/api/3/action/datastore_search',
                        json={
                            "resource_id": "5e87a7a1-2f6f-41c1-8aec-7216d52a6cf6",
                            "filters": {
                                "tozeret_cd": [
                                    str(result['tozeret_cd']).zfill(4)
                                ],
                                "degem_cd": [
                                    str(result['degem_cd']).zfill(4)
                                ],
                                "shnat_yitzur": [
                                    str(result['shnat_yitzur'])
                                ]
                            },
                            "limit": 2,
                            "offset": 0
                        }
                ) as r:
                    final = (await r.json())['result']['records']
                    result.update(final[0])
                    return result
            except IndexError:
                print(f"Car not found in gov db {license_plate_number}")
                return None


@app.get("/cars/{license_plate_number}", response_model=CarModel, tags=['cars'])
async def show_car(license_plate_number: str):
    car = await CARS.find_one({"license_plate_number": license_plate_number})

    if car is None:
        raise HTTPException(status_code=404, detail=f"Car {license_plate_number} not found")

    return car


@app.put("/cars/{license_plate_number}", response_model=CarModel, tags=['cars'])
async def update_car(license_plate_number: str, bg_tasks: BackgroundTasks, car: UpdateCarModel = Body(...)):
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


# /items

@app.get("/items", response_model=list[ItemModel], tags=['items'])
async def get_items():
    return await ITEMS.find().to_list(length=None)


@app.post("/items", response_model=ItemModel, status_code=HTTPStatus.CREATED, tags=['items'])
async def add_item(item: ItemModel):
    item = jsonable_encoder(item)
    new = await ITEMS.insert_one(item)
    return await ITEMS.find_one({"_id": new.inserted_id})


@app.get("/items/{item_id}", response_model=ItemModel, tags=['items'])
async def show_item(item_id: str):
    item = await ITEMS.find_one({"_id": item_id})

    if item is None:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")

    return item


@app.put("/items/{item_id}", response_model=ItemModel, tags=['items'])
async def update_item(item_id: str, item: UpdateItemModel = Body(...)):
    new_item = item.dict()

    existing = await ITEMS.find_one({"_id": item_id}, projection={"_id": 1})
    if existing is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"Item {item_id} not found")

    await ITEMS.update_one({"_id": item_id}, {"$set": new_item})

    return await ITEMS.find_one({"_id": item_id})


@app.delete("/items/{item_id}", tags=['items'])
async def delete_item(item_id: str):
    result = await ITEMS.delete_one({"_id": item_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="No such item")

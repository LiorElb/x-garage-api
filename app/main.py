from http import HTTPStatus

import aiohttp
from fastapi import FastAPI, HTTPException, Body, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware

from models.car_model import CarModel, UpdateCarModel
from models.customer_model import CustomerModel, UpdateCustomerModel
from models.supplier_model import SupplierModel, UpdateSupplierModel
from app.mongo_client import CUSTOMERS, SUPPLIER, CARS, Storage, Used, Tipul, Repairs, Area, Camera, Category
from models.item_model import ItemModel, UpdateItemModel
from models.used_model import UsedModel, UpdateUsedModel
from models.tipulim_modal import TipulModel, UpdateTipulModel
from models.repairs_model import RepairModel, UpdateRepairModel
from models.area_model import AreaModel, UpdateAreaModel
from models.camera_model import CameraModel, UpdateCameraModel
from models.storagecategory_model import StorageCategoryModel, UpdateStorageCategoryModel

app = FastAPI(version="0.6.9")

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


# /camera

@app.get("/camera", response_model=list[CameraModel], tags=['camera'])
async def get_camera():
    return await Camera.find().to_list(length=None)


@app.post("/camera", response_model=CameraModel, status_code=HTTPStatus.CREATED, tags=['camera'])
async def add_camera(item: CameraModel):
    item = jsonable_encoder(item)
    new = await Camera.insert_one(item)
    return await Camera.find_one({"_id": new.inserted_id})


@app.delete("/camera/{customer_id}", tags=['camera'])
async def delete_camera(customer_id: str):
    result = await Camera.delete_one({"_id": customer_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail="No such customer")


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
        raise HTTPException(
            status_code=404, detail=f"Customer {customer_id} not found")

    return customer


@app.put("/customers/{customer_id}", response_model=CustomerModel, tags=['customers'])
async def update_customer(customer_id: str, customer: UpdateCustomerModel = Body(...)):
    new_customer = customer.dict()

    existing = await CUSTOMERS.find_one({"_id": customer_id}, projection={"_id": 1})
    if existing is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail=f"Customer {customer_id} not found")

    if 'cars' in new_customer:
        await assert_cars_dont_belong_to_another_customer(new_customer['cars'], existing['_id'])

    await CUSTOMERS.update_one({"_id": customer_id}, {"$set": new_customer})

    return await CUSTOMERS.find_one({"_id": customer_id})


@app.delete("/customers/{customer_id}", tags=['customers'])
async def delete_customer(customer_id: str):
    result = await CUSTOMERS.delete_one({"_id": customer_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail="No such customer")


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
        raise HTTPException(status_code=HTTPStatus.CONFLICT,
                            detail='Car already exists')

    return await get_cars_by_id(customer_id)


@app.delete("/customers/{customer_id}/cars/{plate_number_to_delete}", tags=['customers'])
async def remove_car_for_customer(customer_id: str, plate_number_to_delete: str):
    result = await CUSTOMERS.update_one(
        {"_id": customer_id},
        update={"$pull": {"cars": plate_number_to_delete}}
    )

    if result.modified_count == 0:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='No such car')

    return await get_cars_by_id(customer_id)


async def assert_cars_dont_belong_to_another_customer(license_plate_numbers: list[str], allowed_id: str = None) -> None:
    existing = await CUSTOMERS.find_one(
        {"cars": {"$in": license_plate_numbers},
         "_id": {"$ne": allowed_id}}
    )

    if existing is not None:
        raise HTTPException(status_code=HTTPStatus.CONFLICT,
                            detail="license number already exists")


async def get_cars_by_id(customer_id) -> list[str]:
    customer = await CUSTOMERS.find_one({"_id": customer_id})
    try:
        return customer['cars']
    except TypeError:  # NoneType
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail="No such customer")


# /cars

@app.get("/cars", response_model=list[CarModel], tags=['cars'])
async def get_cars():
    return await CARS.find().to_list(length=None)


@app.get("/cars/types", response_model=list[list[str | None] | None], tags=['cars'])
async def get_car_types(extended: bool = False):
    return await CARS.distinct(f'government_data.{"tozeret_nm" if extended else "tozar"}', f'government_data.{"shnat_yitzur" if extended else "moed_aliya_lakvish"}')


@app.post("/cars", response_model=CarModel, status_code=HTTPStatus.CREATED, tags=['cars'])
async def add_car(car: CarModel, bg_tasks: BackgroundTasks):
    car = jsonable_encoder(car)
    new = await CARS.insert_one(car)
    new_car = await CARS.find_one(
        {"_id": new.inserted_id},
        projection={"license_plate_number": 1}
    )
    bg_tasks.add_task(enrich_car, new.inserted_id,
                      new_car['license_plate_number'])
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
                    final[0].update(result)
                    return final[0]
            except IndexError:
                print(f"Car not found in gov db {license_plate_number}")
                return None


@app.get("/cars/{license_plate_number}", response_model=CarModel, tags=['cars'])
async def show_car(license_plate_number: str):
    car = await CARS.find_one({"license_plate_number": license_plate_number})

    if car is None:
        raise HTTPException(
            status_code=404, detail=f"Car {license_plate_number} not found")

    return car


@app.put("/cars/{license_plate_number}", response_model=CarModel, tags=['cars'])
async def update_car(license_plate_number: str, bg_tasks: BackgroundTasks, car: UpdateCarModel = Body(...)):
    new_car = car.dict()

    existing = await CARS.find_one(
        {"license_plate_number": license_plate_number},
        projection={"_id": 0, "license_plate_number": 1}
    )
    if existing is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail=f"Car {license_plate_number} not found")

    await CARS.update_one({"license_plate_number": license_plate_number}, {"$set": new_car})

    return await CARS.find_one({"license_plate_number": license_plate_number})


@app.delete("/cars/{license_plate_number}", tags=['cars'])
async def delete_car(license_plate_number: str):
    result = await CARS.delete_one({"license_plate_number": license_plate_number})

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="No such car")

    if result.deleted_count != 1:
        raise HTTPException(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail="Deleted more than one car!")


# /storage

@app.get("/storage", response_model=list[ItemModel], tags=['storage'])
async def get_items():
    return await Storage.find().to_list(length=None)


@app.post("/storage", response_model=ItemModel, status_code=HTTPStatus.CREATED, tags=['storage'])
async def add_item(item: ItemModel):
    item = jsonable_encoder(item)
    new = await Storage.insert_one(item)
    return await Storage.find_one({"_id": new.inserted_id})


@app.get("/storage/{item_id}", response_model=ItemModel, tags=['storage'])
async def show_item(item_id: str):
    item = await Storage.find_one({"_id": item_id})

    if item is None:
        raise HTTPException(
            status_code=404, detail=f"Item {item_id} not found")

    return item


@app.put("/storage/{item_id}", response_model=ItemModel, tags=['storage'])
async def update_item(item_id: str, item: UpdateItemModel = Body(...)):
    new_item = item.dict()

    existing = await Storage.find_one({"_id": item_id}, projection={"_id": 1})
    if existing is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail=f"Item {item_id} not found")

    await Storage.update_one({"_id": item_id}, {"$set": new_item})

    return await Storage.find_one({"_id": item_id})


@app.delete("/storage/{item_id}", tags=['storage'])
async def delete_item(item_id: str):
    result = await Storage.delete_one({"_id": item_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail="No such item")

# /usedItems


@app.get("/used", response_model=list[UsedModel], tags=['used'])
async def get_used():
    return await Used.find().to_list(length=None)


@app.post("/used", response_model=UsedModel, status_code=HTTPStatus.CREATED, tags=['used'])
async def add_used(item: UsedModel):
    item = jsonable_encoder(item)
    new = await Used.insert_one(item)
    return await Used.find_one({"_id": new.inserted_id})


@app.get("/used/{item_id}", response_model=UsedModel, tags=['used'])
async def show_used(item_id: str):
    item = await Used.find_one({"_id": item_id})

    if item is None:
        raise HTTPException(
            status_code=404, detail=f"Used {item_id} not found")

    return item


@app.put("/used/{item_id}", response_model=UsedModel, tags=['used'])
async def update_used(item_id: str, item: UpdateUsedModel = Body(...)):
    new_item = item.dict()

    existing = await Used.find_one({"_id": item_id}, projection={"_id": 1})
    if existing is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail=f"Used {item_id} not found")

    await Used.update_one({"_id": item_id}, {"$set": new_item})

    return await Used.find_one({"_id": item_id})


@app.delete("/used/{item_id}", tags=['used'])
async def delete_used(item_id: str):
    result = await Used.delete_one({"_id": item_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail="No such item")


# /tipulim

@app.get("/tipul", response_model=list[TipulModel], tags=['tipul'])
async def get_tipul():
    return await Tipul.find().to_list(length=None)


@app.post("/tipul", response_model=TipulModel, status_code=HTTPStatus.CREATED, tags=['tipul'])
async def add_tipul(item: TipulModel):
    item = jsonable_encoder(item)
    new = await Tipul.insert_one(item)
    return await Tipul.find_one({"_id": new.inserted_id})


@app.get("/tipul/{item_id}", response_model=TipulModel, tags=['tipul'])
async def show_tipul(item_id: str):
    item = await Tipul.find_one({"_id": item_id})

    if item is None:
        raise HTTPException(
            status_code=404, detail=f"Tipul {item_id} not found")

    return item


@app.put("/tipul/{item_id}", response_model=TipulModel, tags=['tipul'])
async def update_tipul(item_id: str, item: UpdateTipulModel = Body(...)):
    new_item = item.dict()

    existing = await Tipul.find_one({"_id": item_id}, projection={"_id": 1})
    if existing is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail=f"Tipul {item_id} not found")

    await Tipul.update_one({"_id": item_id}, {"$set": new_item})

    return await Tipul.find_one({"_id": item_id})


@app.delete("/tipul/{item_id}", tags=['tipul'])
async def delete_tipul(item_id: str):
    result = await Tipul.delete_one({"_id": item_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail="No such item")

# /Repairs


@app.get("/repairs", response_model=list[RepairModel], tags=['repairs'])
async def get_repairs():
    return await Repairs.find().to_list(length=None)


@app.post("/repairs", response_model=RepairModel, status_code=HTTPStatus.CREATED, tags=['repairs'])
async def add_repairs(item: RepairModel):
    item = jsonable_encoder(item)
    new = await Repairs.insert_one(item)
    return await Repairs.find_one({"_id": new.inserted_id})


@app.get("/repairs/{item_id}", response_model=RepairModel, tags=['repairs'])
async def show_repairs(item_id: str):
    item = await Repairs.find_one({"_id": item_id})

    if item is None:
        raise HTTPException(
            status_code=404, detail=f"repairs {item_id} not found")

    return item


@app.put("/repairs/{item_id}", response_model=RepairModel, tags=['repairs'])
async def update_repairs(item_id: str, item: UpdateRepairModel = Body(...)):
    new_item = item.dict()

    existing = await Repairs.find_one({"_id": item_id}, projection={"_id": 1})
    if existing is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail=f"repairs {item_id} not found")

    await Repairs.update_one({"_id": item_id}, {"$set": new_item})

    return await Repairs.find_one({"_id": item_id})


@app.delete("/repairs/{item_id}", tags=['repairs'])
async def delete_repairs(item_id: str):
    result = await Repairs.delete_one({"_id": item_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail="No such item")


# /category


@app.get("/category", response_model=list[StorageCategoryModel], tags=['category'])
async def get_category():
    return await Category.find().to_list(length=None)


@app.post("/category", response_model=StorageCategoryModel, status_code=HTTPStatus.CREATED, tags=['category'])
async def add_category(item: StorageCategoryModel):
    item = jsonable_encoder(item)
    new = await Category.insert_one(item)
    return await Category.find_one({"_id": new.inserted_id})


@app.get("/category/{item_id}", response_model=StorageCategoryModel, tags=['category'])
async def show_category(item_id: str):
    item = await Category.find_one({"_id": item_id})

    if item is None:
        raise HTTPException(
            status_code=404, detail=f"category {item_id} not found")

    return item


@app.put("/category/{item_id}", response_model=StorageCategoryModel, tags=['category'])
async def update_category(item_id: str, item: UpdateStorageCategoryModel = Body(...)):
    new_item = item.dict()

    existing = await Category.find_one({"_id": item_id}, projection={"_id": 1})
    if existing is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail=f"category {item_id} not found")

    await Category.update_one({"_id": item_id}, {"$set": new_item})

    return await Category.find_one({"_id": item_id})


@app.delete("/category/{item_id}", tags=['category'])
async def delete_category(item_id: str):
    result = await Category.delete_one({"_id": item_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail="No such item")


# /area


@app.get("/area", response_model=list[AreaModel], tags=['area'])
async def get_area():
    return await Area.find().to_list(length=None)


@app.post("/area", response_model=AreaModel, status_code=HTTPStatus.CREATED, tags=['area'])
async def add_area(item: AreaModel):
    item = jsonable_encoder(item)
    new = await Area.insert_one(item)
    return await Area.find_one({"_id": new.inserted_id})


@app.get("/area/{item_id}", response_model=AreaModel, tags=['area'])
async def show_area(item_id: str):
    item = await Area.find_one({"_id": item_id})

    if item is None:
        raise HTTPException(
            status_code=404, detail=f"area {item_id} not found")

    return item


@app.put("/area/{item_id}", response_model=AreaModel, tags=['area'])
async def update_area(item_id: str, item: UpdateAreaModel = Body(...)):
    new_item = item.dict()

    existing = await Area.find_one({"_id": item_id}, projection={"_id": 1})
    if existing is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail=f"area {item_id} not found")

    await Area.update_one({"_id": item_id}, {"$set": new_item})

    return await Area.find_one({"_id": item_id})


@app.delete("/area/{item_id}", tags=['area'])
async def delete_area(item_id: str):
    result = await Area.delete_one({"_id": item_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail="No such item")


# /Supplier


@app.get("/supplier", response_model=list[SupplierModel], tags=['supplier'])
async def get_supplier():
    return await SUPPLIER.find().to_list(length=None)


@app.post("/supplier", response_model=SupplierModel, status_code=HTTPStatus.CREATED, tags=['supplier'])
async def add_supplier(item: SupplierModel):
    item = jsonable_encoder(item)
    new = await SUPPLIER.insert_one(item)
    return await SUPPLIER.find_one({"_id": new.inserted_id})


@app.get("/supplier/{item_id}", response_model=SupplierModel, tags=['supplier'])
async def show_supplier(item_id: str):
    item = await SUPPLIER.find_one({"_id": item_id})

    if item is None:
        raise HTTPException(
            status_code=404, detail=f"supplier {item_id} not found")

    return item


@app.put("/supplier/{item_id}", response_model=SupplierModel, tags=['supplier'])
async def update_supplier(item_id: str, item: UpdateSupplierModel = Body(...)):
    new_item = item.dict()

    existing = await SUPPLIER.find_one({"_id": item_id}, projection={"_id": 1})
    if existing is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail=f"supplier {item_id} not found")

    await SUPPLIER.update_one({"_id": item_id}, {"$set": new_item})

    return await SUPPLIER.find_one({"_id": item_id})


@app.delete("/supplier/{item_id}", tags=['supplier'])
async def delete_supplier(item_id: str):
    result = await SUPPLIER.delete_one({"_id": item_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail="No such item")

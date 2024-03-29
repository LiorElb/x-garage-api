from http import HTTPStatus

import aiohttp
from fastapi import FastAPI, HTTPException, Body, BackgroundTasks, Header
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware

from models.car_model import CarModel, UpdateCarModel
from models.customer_model import CustomerModel, UpdateCustomerModel
from models.supplier_model import SupplierModel, UpdateSupplierModel
from app.mongo_client import CUSTOMERS, SUPPLIER, CARS, Storage, Used, Tools, Tipul, TipulGroup, Repairs, RepairsFinish, Area, Camera, Category, CategoryTools, ErrorCode
from models.item_model import ItemModel, UpdateItemModel
from models.used_model import UsedModel, UpdateUsedModel
from models.tools_model import ToolsModel, UpdateToolsModel
from models.tipulim_modal import TipulModel, UpdateTipulModel
from models.tipulim_group_modal import TipulGroupModel, UpdateTipulGroupModel
from models.repairs_model import RepairModel, UpdateRepairModel
from models.repairs_finish import RepairFinishModel
from models.error_code_model import ErrorCodeModel
from models.area_model import AreaModel, UpdateAreaModel
from models.camera_model import CameraModel, UpdateCameraModel
from models.storagecategory_model import StorageCategoryModel, UpdateStorageCategoryModel
from models.toolscategory_model import ToolsCategoryModel, UpdateToolsCategoryModel

app = FastAPI(version="0.8.2")
key = "ea5e6rtyuhjbvxsre76oiukjhbvdrt576tiyukhytyohbvcjxa7wtfikaw"
origins = [
    "*"  # TODO: Authentication - make sure its safe with chosen auth method
]

# allowed_origins = ["http://localhost:8080", "https://example.com"]
# allowed_headers = ["Content-Type", "Authorization"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# get_camera(* , security_key: str = Header(None)):
# Validate the security key
# if security_key != key:
#     raise HTTPException(status_code=401, detail="Invalid security key")
#

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


@app.get("/customersbycar/{plate_num}", tags=['customers'])
async def show_customer(plate_num: str):
    customers = await CUSTOMERS.find({"cars": plate_num}).to_list(length=None)
    if customers is None:
        raise HTTPException(
            status_code=404, detail=f"car {plate_num} not found")

    return customers


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


@app.get("/cars/types/{car_num}", tags=['cars'])
async def get_car_type(car_num: str):
    car = await CARS.find_one({"license_plate_number": car_num})
    if car is None:
        raise HTTPException(
            status_code=404, detail=f"Car {car_num} not found")
    x = car["government_data"]["tozar"]
    y = car["government_data"]["kinuy_mishari"]
    z = car["government_data"]["shnat_yitzur"]
    dic = {'tozar': x, 'kinuy_mishari': y, 'shnat_yitzur': z}
    return (dic)


@app.get("/cars/types", tags=['cars'])
async def get_car_types():
    cars = await CARS.find().to_list(length=None)
    list = []
    for car in cars:
        if car["government_data"] is not None:
            x = car["government_data"]["tozar"]
            y = car["government_data"]["kinuy_mishari"]
            # z = car["government_data"]["shnat_yitzur"]
            dic = {'tozar': x, 'kinuy_mishari': y}
            list.append(dic)
    # return list
    new_list = []
    for one_student_choice in list:
        if one_student_choice not in new_list:
            new_list.append(one_student_choice)
    return new_list


# async def get_car_types():
#     return await CARS.distinct(f'government_data.{"tozar"}')


@app.post("/cars", response_model=CarModel, status_code=HTTPStatus.CREATED, tags=['cars'])
async def add_car(car: CarModel, bg_tasks: BackgroundTasks):
    car = jsonable_encoder(car)

    existing_car = await CARS.find_one(
        {"license_plate_number": car["license_plate_number"]}
    )
    if existing_car:
        # If the license plate number already exists, continue with the existing _id
        _id = existing_car["_id"]
    else:
        # If the license plate number does not exist, insert a new car
        new = await CARS.insert_one(car)
        _id = new.inserted_id
    new_car = await CARS.find_one(
        {"_id": _id},
        projection={"license_plate_number": 1}
    )
    bg_tasks.add_task(enrich_car, _id,
                      new_car['license_plate_number'])

    new_car_result = await CARS.find_one(
        {"_id": _id}
    )
    return new_car_result


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
# if not found look here -  "mispar_rechev": [license_plate_number]
# 03adc637-b6fe-402b-9937-7c3d3afc9140
# ואם לא אז צריך לחפש פה
# resource_id=cd3acc5c-03c3-4c89-9c54-d40f93c0d790
# ואם לא אז לבדוק אם הרכב ירד מהכביש פה
# resource_id=851ecab1-0622-4dbe-a6c7-f950cf82abf9
# ואם הוא ירד מהכביש תעדכן את פפוש איזה סעיף צריך לבדוק

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


@app.get("/cars/{license_plate_number}", tags=['cars'])
async def show_car(license_plate_number: str):
    car = await CARS.find_one({"license_plate_number": license_plate_number})

    if car is None:
        return {"detail": f"Car {license_plate_number} not found"}
    else:
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
async def get_storage():
    return await Storage.find().to_list(length=None)


@app.post("/storage", response_model=ItemModel, status_code=HTTPStatus.CREATED, tags=['storage'])
async def add_storage(item: ItemModel):
    item = jsonable_encoder(item)
    new = await Storage.insert_one(item)
    return await Storage.find_one({"_id": new.inserted_id})


@app.get("/storage/{item_id}", response_model=ItemModel, tags=['storage'])
async def show_storage(item_id: str):
    item = await Storage.find_one({"_id": item_id})
    if item is None:
        raise HTTPException(
            status_code=404, detail=f"storage {item_id} not found")
    return item


@app.get("/storagebarcode/{item_id}", response_model=ItemModel, tags=['storage'])
async def show_storage(item_id: str):
    item = await Storage.find_one({"barcode": item_id})
    if item is None:
        raise HTTPException(
            status_code=404, detail=f"storage {item_id} not found")
    return item


@app.get("/storagebycategory/{category_id}", response_model=list[ItemModel], tags=['storage'])
async def show_storage(category_id: str):
    item = await Storage.find({"category": category_id}).to_list(length=None)
    if item is None:
        raise HTTPException(
            status_code=404, detail=f"storage {category_id} not found")
    return item


@app.put("/storage/{item_id}", response_model=ItemModel, tags=['storage'])
async def update_storage(item_id: str, item: UpdateItemModel = Body(...)):
    new_item = item.dict()

    existing = await Storage.find_one({"_id": item_id}, projection={"_id": 1})
    if existing is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail=f"storage {item_id} not found")

    await Storage.update_one({"_id": item_id}, {"$set": new_item})

    return await Storage.find_one({"_id": item_id})


@app.delete("/storage/{item_id}", tags=['storage'])
async def delete_storage(item_id: str):
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
            status_code=404, detail=f"used {item_id} not found")

    return item


@app.put("/used/{item_id}", response_model=UsedModel, tags=['used'])
async def update_used(item_id: str, item: UpdateUsedModel = Body(...)):
    new_item = item.dict()

    existing = await Used.find_one({"_id": item_id}, projection={"_id": 1})
    if existing is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail=f"used {item_id} not found")

    await Used.update_one({"_id": item_id}, {"$set": new_item})

    return await Used.find_one({"_id": item_id})


@app.delete("/used/{item_id}", tags=['used'])
async def delete_used(item_id: str):
    result = await Used.delete_one({"_id": item_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail="No such item")


# /ToolsItems

@app.get("/tools", response_model=list[ToolsModel], tags=['tools'])
async def get_tools():
    return await Tools.find().to_list(length=None)


@app.post("/tools", response_model=ToolsModel, status_code=HTTPStatus.CREATED, tags=['tools'])
async def add_tools(item: ToolsModel):
    item = jsonable_encoder(item)
    new = await Tools.insert_one(item)
    return await Tools.find_one({"_id": new.inserted_id})


@app.get("/tools/{item_id}", response_model=ToolsModel, tags=['tools'])
async def show_tools(item_id: str):
    item = await Tools.find_one({"_id": item_id})

    if item is None:
        raise HTTPException(
            status_code=404, detail=f"tools {item_id} not found")

    return item


@app.put("/tools/{item_id}", response_model=ToolsModel, tags=['tools'])
async def update_tools(item_id: str, item: UpdateToolsModel = Body(...)):
    new_item = item.dict()

    existing = await Tools.find_one({"_id": item_id}, projection={"_id": 1})
    if existing is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail=f"tools {item_id} not found")

    await Tools.update_one({"_id": item_id}, {"$set": new_item})

    return await Tools.find_one({"_id": item_id})


@app.delete("/tools/{item_id}", tags=['tools'])
async def delete_tools(item_id: str):
    result = await Tools.delete_one({"_id": item_id})

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
            status_code=404, detail=f"tipul {item_id} not found")

    return item


@app.put("/tipul/{item_id}", response_model=TipulModel, tags=['tipul'])
async def update_tipul(item_id: str, item: UpdateTipulModel = Body(...)):
    new_item = item.dict()

    existing = await Tipul.find_one({"_id": item_id}, projection={"_id": 1})
    if existing is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail=f"tipul {item_id} not found")

    await Tipul.update_one({"_id": item_id}, {"$set": new_item})

    return await Tipul.find_one({"_id": item_id})


@app.delete("/tipul/{item_id}", tags=['tipul'])
async def delete_tipul(item_id: str):
    result = await Tipul.delete_one({"_id": item_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail="No such item")


# /tipulimgroup

@app.get("/tipulgroup", response_model=list[TipulGroupModel], tags=['tipulgroup'])
async def get_tipul_group():
    return await TipulGroup.find().to_list(length=None)


@app.post("/tipulgroup", response_model=TipulGroupModel, status_code=HTTPStatus.CREATED, tags=['tipulgroup'])
async def add_tipul_group(item: TipulGroupModel):
    item = jsonable_encoder(item)
    new = await TipulGroup.insert_one(item)
    return await TipulGroup.find_one({"_id": new.inserted_id})


@app.get("/tipulgroup/{item_id}", response_model=TipulGroupModel, tags=['tipulgroup'])
async def show_tipul_group(item_id: str):
    item = await TipulGroup.find_one({"_id": item_id})

    if item is None:
        raise HTTPException(
            status_code=404, detail=f"tipul group {item_id} not found")

    return item


@app.put("/tipulgroup/{item_id}", response_model=TipulGroupModel, tags=['tipulgroup'])
async def update_tipul_group(item_id: str, item: UpdateTipulGroupModel = Body(...)):
    new_item = item.dict()

    existing = await TipulGroup.find_one({"_id": item_id}, projection={"_id": 1})
    if existing is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail=f"tipul group {item_id} not found")

    await TipulGroup.update_one({"_id": item_id}, {"$set": new_item})

    return await TipulGroup.find_one({"_id": item_id})


@app.delete("/tipulgroup/{item_id}", tags=['tipulgroup'])
async def delete_tipul(item_id: str):
    result = await TipulGroup.delete_one({"_id": item_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail="No such item")


# /repairs


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


# /repairsfinish


@app.get("/repairsfinish", response_model=list[RepairFinishModel], tags=['repairsfinish'])
async def get_repairsfinish():
    return await RepairsFinish.find().to_list(length=None)


@app.post("/repairsfinish", response_model=RepairFinishModel, status_code=HTTPStatus.CREATED, tags=['repairsfinish'])
async def add_repairsfinish(item: RepairFinishModel):
    item = jsonable_encoder(item)
    new = await RepairsFinish.insert_one(item)
    return await RepairsFinish.find_one({"_id": new.inserted_id})


@app.get("/repairsfinish/{item_id}", response_model=list[RepairFinishModel], tags=['repairsfinish'])
async def show_repairsfinish(item_id: str):
    item = await RepairsFinish.find({"license_plate_number": item_id}).to_list(length=None)

    if item is None:
        raise HTTPException(
            status_code=404, detail=f"repairsfinish {item_id} not found")

    return item


@app.delete("/repairsfinish/{item_id}", tags=['repairsfinish'])
async def delete_repairsfinish(item_id: str):
    result = await RepairsFinish.delete_one({"_id": item_id})

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
    item['number'] = await Category.count_documents({})
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


# /categorytools


@app.get("/categorytools", response_model=list[ToolsCategoryModel], tags=['categorytools'])
async def get_categorytools():
    return await CategoryTools.find().to_list(length=None)


@app.post("/categorytools", response_model=ToolsCategoryModel, status_code=HTTPStatus.CREATED, tags=['categorytools'])
async def add_categorytools(item: ToolsCategoryModel):
    item = jsonable_encoder(item)
    item['number'] = await Category.count_documents({})
    new = await CategoryTools.insert_one(item)
    return await CategoryTools.find_one({"_id": new.inserted_id})


@app.get("/categorytools/{item_id}", response_model=ToolsCategoryModel, tags=['categorytools'])
async def show_categorytools(item_id: str):
    item = await CategoryTools.find_one({"_id": item_id})

    if item is None:
        raise HTTPException(
            status_code=404, detail=f"categorytools {item_id} not found")

    return item


@app.put("/categorytools/{item_id}", response_model=ToolsCategoryModel, tags=['categorytools'])
async def update_categorytools(item_id: str, item: UpdateToolsCategoryModel = Body(...)):
    new_item = item.dict()

    existing = await CategoryTools.find_one({"_id": item_id}, projection={"_id": 1})
    if existing is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail=f"categorytools {item_id} not found")

    await CategoryTools.update_one({"_id": item_id}, {"$set": new_item})

    return await CategoryTools.find_one({"_id": item_id})


@app.delete("/categorytools/{item_id}", tags=['categorytools'])
async def delete_categorytools(item_id: str):
    result = await CategoryTools.delete_one({"_id": item_id})

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


# /supplier


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


# /errors

@app.get("/errorcode", response_model=list[ErrorCodeModel], tags=['errorcode'])
async def get_errorcode():
    return await ErrorCode.find().to_list(length=None)


@app.post("/errorcode", response_model=ErrorCodeModel, status_code=HTTPStatus.CREATED, tags=['errorcode'])
async def add_errorcode(item: ErrorCodeModel):
    item.code = item.code.lower()
    item = jsonable_encoder(item)
    new = await ErrorCode.insert_one(item)
    return await ErrorCode.find_one({"_id": new.inserted_id})


@app.get("/errorcode/{item_id}", response_model=list[ErrorCodeModel], tags=['errorcode'])
async def show_errorcode(item_id: str):
    item_id = item_id.lower()
    item = await ErrorCode.find({"code": item_id}).to_list(length=None)
    if item is None:
        raise HTTPException(
            status_code=404, detail=f"errorcode {item_id} not found")
    return item

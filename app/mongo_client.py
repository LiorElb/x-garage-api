import os
import motor.motor_asyncio as motor

MONGO_CONNECTION_STR = os.getenv('GARAGE_MONGO_CONNECTION_STR')

if not MONGO_CONNECTION_STR:
    raise EnvironmentError("Please define GARAGE_MONGO_CONNECTION_STR in env")

client = motor.AsyncIOMotorClient(MONGO_CONNECTION_STR)
CUSTOMERS = client['main']['customers']
SUPPLIER = client['main']['supplier']
CARS = client['main']['cars']
Storage = client['main']['storage']
Used = client['main']['used']
Tipul = client['main']['tipul']
TipulGroup = client['main']['tipulgroup']
Repairs = client['main']['repairs']
RepairsFinish = client['main']['repairsfinish']
Area = client['main']['area']
Camera = client['main']['camera']
Category = client['main']['category']
ErrorCode = client['main']['errorcode']

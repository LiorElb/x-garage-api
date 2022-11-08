import os
import motor.motor_asyncio as motor

MONGO_CONNECTION_STR = os.getenv('GARAGE_MONGO_CONNECTION_STR')

if not MONGO_CONNECTION_STR:
    raise EnvironmentError("Please define GARAGE_MONGO_CONNECTION_STR in env")

client = motor.AsyncIOMotorClient(MONGO_CONNECTION_STR)
CUSTOMERS = client['main']['customers']
CARS = client['main']['cars']
ITEMS = client['main']['items']
Used = client['main']['used']
Tipul = client['main']['tipul']

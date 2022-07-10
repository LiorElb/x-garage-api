import os
import motor.motor_asyncio as motor

MONGO_HOST = os.getenv('GARAGE_MONGO_HOST')
MONGO_PORT = os.getenv('GARAGE_MONGO_PORT')

if not all((MONGO_HOST, MONGO_PORT)):
    raise EnvironmentError("Please define GARAGE_MONGO_HOST and GARAGE_MONGO_PORT in env")

client = motor.AsyncIOMotorClient(f'mongodb://{MONGO_HOST}:{MONGO_PORT}/')
CUSTOMERS = client['main']['customers']
CARS = client['main']['cars']

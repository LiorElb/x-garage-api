import os
import motor.motor_asyncio as motor

MONGO_HOST = os.getenv('GARAGE_MONGO_HOST', 'localhost')
MONGO_PORT = os.getenv('GARAGE_MONGO_PORT', '27017')
client = motor.AsyncIOMotorClient(f'mongodb://{MONGO_HOST}:{MONGO_PORT}/')
CUSTOMERS = client['main']['customers']
CARS = client['main']['cars']

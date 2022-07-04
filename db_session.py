import os

from pymongo import MongoClient

MONGO_HOST = os.getenv('GARAGE_MONGO_HOST', 'localhost:27017/')


class DBSession:
    _client: MongoClient

    def __init__(self, client: MongoClient = None, db=None):
        if client is None:
            client = MongoClient(f'mongodb://{MONGO_HOST}')
        self._client = client
        self._db = db

    def select_db(self, db: str):
        self._db = self._client[db]

    @property
    def db(self):
        if self._db is None:
            raise ValueError('DB is not set, please select a db before using the session')
        return self._db

    def find(self, collection: str, *args, **kwargs):
        return list(self.db[collection].find(*args, **kwargs))

    def insert(self, collection: str, *args, **kwargs):

        self.db[collection].insert(*args, **kwargs)

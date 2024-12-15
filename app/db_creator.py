import json
from pymongo import MongoClient

# MongoDB конфигурация
MONGO_URI = "mongodb://mongo:27017"
DB_NAME = "indicators_database"

def writeToMongo(data: list, collection_name="data") -> None:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    db.drop_collection(collection_name)
    collection = db[collection_name]
    
    # Вставляем данные в MongoDB
    collection.insert_many(data)

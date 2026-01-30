from pymongo import MongoClient
from config import MONGO_URI

client = MongoClient(MONGO_URI)
db = client["AiBot"]

users_collection = db["users"]
chats_collection = db["chats"]
files_collection = db["files"]

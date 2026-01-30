import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WEB_SEARCH_API_KEY = os.getenv("BRAVE_SEARCH_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

if not all([BOT_TOKEN, GEMINI_API_KEY, WEB_SEARCH_API_KEY, MONGO_URI]):
    raise ValueError("One or more environment variables are missing! Check your .env file.")

client = MongoClient(MONGO_URI)
db = client["AiBot"]

users_collection = db["users"]
chats_collection = db["chats"]
files_collection = db["files"]

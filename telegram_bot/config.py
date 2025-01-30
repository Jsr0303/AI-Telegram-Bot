import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load .env file
load_dotenv()

# Get API Keys and Tokens from Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WEB_SEARCH_API_KEY = os.getenv("WEB_SEARCH_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

# Check if any variable is missing
if not all([BOT_TOKEN, GEMINI_API_KEY, WEB_SEARCH_API_KEY, MONGO_URI]):
    raise ValueError("One or more environment variables are missing! Check your .env file.")

# MongoDB setup
client = MongoClient(MONGO_URI)
db = client['AiBot']  # Replace with your database name

# Define collections
users_collection = db['users']
chats_collection = db['chats']
files_collection = db['files']

# Print confirmation (optional)
print("Configuration loaded successfully!")





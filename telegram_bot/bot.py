'''import logging
import requests
from datetime import datetime
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext
from textblob import TextBlob
from transformers import pipeline
from config import BOT_TOKEN, GEMINI_API_KEY, users_collection, chats_collection, files_collection, WEB_SEARCH_API_KEY
from pymongo import MongoClient

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Hugging Face Sentiment Pipeline (Alternative to TextBlob)
sentiment_pipeline = pipeline("sentiment-analysis")

# MongoDB setup
client = MongoClient("mongodb+srv://jaikishanrajawat968:Jaikishan@cluster0.fuj0u.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client['AiBot']

# Ensure collections exist or create them
def create_collection_if_not_exists(collection_name):
    if collection_name not in db.list_collection_names():
        db.create_collection(collection_name)

# Start Command
def start(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    first_name = update.message.chat.first_name
    username = update.message.chat.username
    
    if not users_collection.find_one({"chat_id": chat_id}):
        users_collection.insert_one({
            "chat_id": chat_id,
            "first_name": first_name,
            "username": username,
            "phone_number": None
        })
        reply_markup = ReplyKeyboardMarkup(
            [[KeyboardButton("Share Phone Number", request_contact=True)]],
            resize_keyboard=True
        )
        update.message.reply_text("Welcome! Please share your phone number:", reply_markup=reply_markup)
    else:
        update.message.reply_text("Welcome back!")

# Contact Handler
def contact_handler(update: Update, context: CallbackContext):
    contact = update.message.contact
    chat_id = update.message.chat_id
    
    if contact:
        users_collection.update_one({"chat_id": chat_id}, {"$set": {"phone_number": contact.phone_number}})
        update.message.reply_text("Phone number saved. Thank you!")

# Sentiment Analysis Function
def analyze_sentiment(text):
    """Analyzes sentiment using TextBlob or Hugging Face Transformers."""
    try:
        # Option 1: Using Hugging Face Transformers
        sentiment_result = sentiment_pipeline(text)[0]
        return sentiment_result['label'], sentiment_result['score']
    except:
        # Option 2: Fallback to TextBlob if Transformers fail
        sentiment = TextBlob(text).sentiment
        polarity = sentiment.polarity
        category = "Positive" if polarity > 0.1 else "Negative" if polarity < -0.1 else "Neutral"
        return category, polarity

# Chat Handler
def chat(update: Update, context: CallbackContext):
    user_input = update.message.text
    chat_id = update.message.chat_id

    # Analyze Sentiment
    sentiment_category, sentiment_score = analyze_sentiment(user_input)

    # Generate Response from Gemini
    response = requests.post("https://api.generativeai.com/generate", headers={
        "Authorization": f"Bearer {GEMINI_API_KEY}"
    }, json={"prompt": user_input}).json()

    bot_response = response.get('response', "Sorry, I couldn't understand that.")

    # Save chat history with sentiment analysis
    chats_collection.insert_one({
        "chat_id": chat_id,
        "user_input": user_input,
        "sentiment_category": sentiment_category,
        "sentiment_score": sentiment_score,
        "bot_response": bot_response,
        "timestamp": datetime.utcnow()
    })

    # Reply to the user with sentiment information
    update.message.reply_text(f"Sentiment: {sentiment_category} ({sentiment_score:.2f})\n{bot_response}")

# Web Search Handler
def web_search(update: Update, context: CallbackContext):
    query = " ".join(context.args)
    
    # Mock Web Search API (Replace with actual API calls)
    search_results = requests.get("https://api.bing.microsoft.com/v7.0/search", headers={
        "Ocp-Apim-Subscription-Key": WEB_SEARCH_API_KEY
    }, params={"q": query}).json()

    summary = "\n".join([f"{result['name']}: {result['url']}" for result in search_results.get('webPages', {}).get('value', [])[:3]])

    update.message.reply_text(f"Top results:\n{summary}" if summary else "No results found.")

# File Handler
def file_handler(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    file = update.message.document or update.message.photo[-1] if update.message.photo else None

    if file:
        file_id = file.file_id
        file_name = file.file_name if update.message.document else f"photo_{file_id}.jpg"

        # Download file
        file_path = context.bot.get_file(file_id).download(file_name)

        # Analyze with Gemini (Mock Example)
        description = f"Processed {file_name}"

        # Save file metadata
        files_collection.insert_one({
            "chat_id": chat_id,
            "file_name": file_name,
            "description": description,
            "timestamp": datetime.utcnow()
        })

        update.message.reply_text(f"File received: {file_name}. Description: {description}")

# Main Function
def main():
    # Create collections if they do not exist
    create_collection_if_not_exists("users_collection")
    create_collection_if_not_exists("chats_collection")
    create_collection_if_not_exists("files_collection")

    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.contact, contact_handler))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, chat))
    dp.add_handler(CommandHandler("websearch", web_search))
    dp.add_handler(MessageHandler(Filters.document | Filters.photo, file_handler))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()'''


'''
import os
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from textblob import TextBlob
from transformers import pipeline

# Load environment variables
load_dotenv()

# Get API Keys and Tokens from .env
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WEB_SEARCH_API_KEY = os.getenv("WEB_SEARCH_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

if not all([BOT_TOKEN, GEMINI_API_KEY, WEB_SEARCH_API_KEY, MONGO_URI]):
    raise ValueError("Missing one or more environment variables! Check your .env file.")

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB setup
client = MongoClient(MONGO_URI)
db = client['AiBot']
users_collection = db['users']
chats_collection = db['chats']
files_collection = db['files']

# Hugging Face Sentiment Pipeline
sentiment_pipeline = pipeline("sentiment-analysis")

async def start(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    first_name = update.message.chat.first_name
    username = update.message.chat.username

    if not users_collection.find_one({"chat_id": chat_id}):
        users_collection.insert_one({
            "chat_id": chat_id,
            "first_name": first_name,
            "username": username,
            "phone_number": None
        })
        reply_markup = ReplyKeyboardMarkup(
            [[KeyboardButton("Share Phone Number", request_contact=True)]],
            resize_keyboard=True
        )
        await update.message.reply_text("Welcome! Please share your phone number:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Welcome back!")

async def contact_handler(update: Update, context: CallbackContext) -> None:
    contact = update.message.contact
    chat_id = update.message.chat_id

    if contact:
        users_collection.update_one({"chat_id": chat_id}, {"$set": {"phone_number": contact.phone_number}})
        await update.message.reply_text("Phone number saved. Thank you!")

async def chat(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text
    chat_id = update.message.chat_id

    sentiment_category, sentiment_score = analyze_sentiment(user_input)
    try:
        response = requests.post("https://api.generativeai.com/generate", headers={
            "Authorization": f"Bearer {GEMINI_API_KEY}"
        }, json={"prompt": user_input}).json()

        bot_response = response.get('response', "Sorry, I couldn't understand that.")
    except Exception as e:
        logger.error(f"Gemini API Error: {e}")
        bot_response = "Sorry, there was an issue generating a response."

    chats_collection.insert_one({
        "chat_id": chat_id,
        "user_input": user_input,
        "sentiment_category": sentiment_category,
        "sentiment_score": sentiment_score,
        "bot_response": bot_response,
        "timestamp": datetime.utcnow()
    })
    
    await update.message.reply_text(f"Sentiment: {sentiment_category} ({sentiment_score})\n{bot_response}")

async def web_search(update: Update, context: CallbackContext) -> None:
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Please provide a search query. Example: /websearch AI trends")
        return

    try:
        search_results = requests.get("https://api.bing.microsoft.com/v7.0/search", headers={
            "Ocp-Apim-Subscription-Key": WEB_SEARCH_API_KEY
        }, params={"q": query}).json()

        results = search_results.get('webPages', {}).get('value', [])[:3]
        summary = "\n".join([f"{result['name']}: {result['url']}" for result in results])

        await update.message.reply_text(f"Top results:\n{summary}" if summary else "No results found.")
    except Exception as e:
        logger.error(f"Web Search Error: {e}")
        await update.message.reply_text("Error fetching search results. Try again later.")

async def file_handler(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    file = update.message.document or (update.message.photo[-1] if update.message.photo else None)
    
    if file:
        file_id = file.file_id
        file_name = file.file_name if update.message.document else f"photo_{file_id}.jpg"

        try:
            file_path = await context.bot.get_file(file_id)
            file_path.download(file_name)
            description = f"Processed {file_name}"

            files_collection.insert_one({
                "chat_id": chat_id,
                "file_name": file_name,
                "description": description,
                "timestamp": datetime.utcnow()
            })

            await update.message.reply_text(f"File received: {file_name}. Description: {description}")
        except Exception as e:
            logger.error(f"File Handling Error: {e}")
            await update.message.reply_text("Error processing the file.")

async def analyze_sentiment(text: str):
    try:
        sentiment_result = sentiment_pipeline(text)[0]
        return sentiment_result['label'], round(sentiment_result['score'], 2)
    except Exception as e:
        logger.error(f"Sentiment Analysis Error: {e}")
        sentiment = TextBlob(text).sentiment.polarity
        category = "Positive" if sentiment > 0.1 else "Negative" if sentiment < -0.1 else "Neutral"
        return category, round(sentiment, 2)

async def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.add_handler(CommandHandler("websearch", web_search))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, file_handler))
    
    logger.info("Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())'''





import os
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from textblob import TextBlob
from transformers import pipeline
import asyncio

# Load environment variables
load_dotenv()

# Get API Keys and Tokens from .env
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WEB_SEARCH_API_KEY = os.getenv("WEB_SEARCH_API_KEY")
MONGO_URI = os.getenv("MONGO_URI")

if not all([BOT_TOKEN, GEMINI_API_KEY, WEB_SEARCH_API_KEY, MONGO_URI]):
    raise ValueError("Missing one or more environment variables! Check your .env file.")

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB setup
client = MongoClient(MONGO_URI)
db = client['AiBot']
users_collection = db['users']
chats_collection = db['chats']
files_collection = db['files']

# Hugging Face Sentiment Pipeline
sentiment_pipeline = pipeline("sentiment-analysis")

async def start(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    first_name = update.message.chat.first_name
    username = update.message.chat.username

    if not users_collection.find_one({"chat_id": chat_id}):
        users_collection.insert_one({
            "chat_id": chat_id,
            "first_name": first_name,
            "username": username,
            "phone_number": None
        })
        reply_markup = ReplyKeyboardMarkup(
            [[KeyboardButton("Share Phone Number", request_contact=True)]],
            resize_keyboard=True
        )
        await update.message.reply_text("Welcome! Please share your phone number:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("Welcome back!")

async def contact_handler(update: Update, context: CallbackContext) -> None:
    contact = update.message.contact
    chat_id = update.message.chat_id

    if contact:
        users_collection.update_one({"chat_id": chat_id}, {"$set": {"phone_number": contact.phone_number}})
        await update.message.reply_text("Phone number saved. Thank you!")

async def chat(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text
    chat_id = update.message.chat_id

    sentiment_category, sentiment_score = analyze_sentiment(user_input)
    try:
        response = requests.post("https://api.generativeai.com/generate", headers={
            "Authorization": f"Bearer {GEMINI_API_KEY}"
        }, json={"prompt": user_input}).json()

        bot_response = response.get('response', "Sorry, I couldn't understand that.")
    except Exception as e:
        logger.error(f"Gemini API Error: {e}")
        bot_response = "Sorry, there was an issue generating a response."

    chats_collection.insert_one({
        "chat_id": chat_id,
        "user_input": user_input,
        "sentiment_category": sentiment_category,
        "sentiment_score": sentiment_score,
        "bot_response": bot_response,
        "timestamp": datetime.utcnow()
    })
    
    await update.message.reply_text(f"Sentiment: {sentiment_category} ({sentiment_score})\n{bot_response}")

async def web_search(update: Update, context: CallbackContext) -> None:
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Please provide a search query. Example: /websearch AI trends")
        return

    try:
        search_results = requests.get("https://api.bing.microsoft.com/v7.0/search", headers={
            "Ocp-Apim-Subscription-Key": WEB_SEARCH_API_KEY
        }, params={"q": query}).json()

        results = search_results.get('webPages', {}).get('value', [])[:3]
        summary = "\n".join([f"{result['name']}: {result['url']}" for result in results])

        await update.message.reply_text(f"Top results:\n{summary}" if summary else "No results found.")
    except Exception as e:
        logger.error(f"Web Search Error: {e}")
        await update.message.reply_text("Error fetching search results. Try again later.")

async def file_handler(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    file = update.message.document or (update.message.photo[-1] if update.message.photo else None)
    
    if file:
        file_id = file.file_id
        file_name = file.file_name if update.message.document else f"photo_{file_id}.jpg"

        try:
            file_path = await context.bot.get_file(file_id)
            file_path.download(file_name)
            description = f"Processed {file_name}"

            files_collection.insert_one({
                "chat_id": chat_id,
                "file_name": file_name,
                "description": description,
                "timestamp": datetime.utcnow()
            })

            await update.message.reply_text(f"File received: {file_name}. Description: {description}")
        except Exception as e:
            logger.error(f"File Handling Error: {e}")
            await update.message.reply_text("Error processing the file.")

async def analyze_sentiment(text: str):
    try:
        sentiment_result = sentiment_pipeline(text)[0]
        return sentiment_result['label'], round(sentiment_result['score'], 2)
    except Exception as e:
        logger.error(f"Sentiment Analysis Error: {e}")
        sentiment = TextBlob(text).sentiment.polarity
        category = "Positive" if sentiment > 0.1 else "Negative" if sentiment < -0.1 else "Neutral"
        return category, round(sentiment, 2)

async def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.add_handler(CommandHandler("websearch", web_search))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, file_handler))
    
    logger.info("Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    try:
        # Running the app directly without asyncio.run()
        asyncio.get_event_loop().run_until_complete(main())
    except RuntimeError as e:
        if "This event loop is already running" in str(e):
            # Handle the situation where the event loop is already running (e.g., Jupyter)
            logger.info("Event loop already running. Running bot in existing loop.")
            loop = asyncio.get_event_loop()
            loop.create_task(main())
            loop.run_forever()
        else:
            raise

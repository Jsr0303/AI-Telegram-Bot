import os
import logging
import requests
import nest_asyncio
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Enable asyncio for Jupyter
nest_asyncio.apply()

# Load environment variables


# API URLs
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
BRAVE_SEARCH_API_URL = "https://api.search.brave.com/res/v1/web/search"

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB setup
client = MongoClient(MONGO_URI)
db = client["AiBot"]
users_collection = db["users"]
chats_collection = db["chats"]
files_collection = db["files"]

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
    
    try:
        payload = {"contents": [{"parts": [{"text": user_input}]}]}
        response = requests.post(
            GEMINI_API_URL,
            headers={"Content-Type": "application/json"},
            json=payload
        ).json()
        bot_response = response.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "Sorry, I couldn't understand that.")
    except Exception as e:
        logger.error(f"Gemini API Error: {e}")
        bot_response = "Sorry, there was an issue generating a response."

    chats_collection.insert_one({
        "chat_id": chat_id,
        "user_input": user_input,
        "bot_response": bot_response,
        "timestamp": datetime.utcnow()
    })
    
    await update.message.reply_text(bot_response)

async def web_search(update: Update, context: CallbackContext) -> None:
    query = " ".join(context.args)
    if not query:
        await update.message.reply_text("Please provide a search query. Example: /websearch AI trends")
        return

    try:
        response = requests.get(
            BRAVE_SEARCH_API_URL,
            headers={"X-Subscription-Token": BRAVE_SEARCH_API_KEY},
            params={"q": query, "count": 5}
        )
        search_results = response.json()
        results = search_results.get("web", {}).get("results", [])[:3]
        
        summary = "\n".join([f"{idx+1}. {res.get('title', 'No Title')}: {res.get('url', 'No URL')}" for idx, res in enumerate(results)])
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
            await file_path.download_to_drive(file_name)
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

async def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.add_handler(CommandHandler("websearch", web_search))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, file_handler))
    
    logger.info("Bot is running...")
    
    await app.run_polling()

# Start the bot in Jupyter Notebook
try:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
except RuntimeError as e:
    if "This event loop is already running" in str(e):
        logger.info("Event loop already running. Running bot in existing loop.")
        asyncio.ensure_future(main())
    else:
        raise

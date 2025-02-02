import os
import logging
import requests
import nest_asyncio
import asyncio
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

# Enable asyncio for Jupyter Notebooks
nest_asyncio.apply()



GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
BRAVE_SEARCH_API_URL = "https://api.search.brave.com/res/v1/web/search"

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sentiment analysis setup
MODEL_NAME = "distilbert/distilbert-base-uncased-finetuned-sst-2-english"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
sentiment_pipeline = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)

async def start(update: Update, context: CallbackContext) -> None:
    """Handles the /start command, prompting the user to share their phone number."""
    reply_markup = ReplyKeyboardMarkup(
        [[KeyboardButton("Share Phone Number", request_contact=True)]],
        resize_keyboard=True
    )
    await update.message.reply_text("Welcome! Please share your phone number:", reply_markup=reply_markup)

async def contact_handler(update: Update, context: CallbackContext) -> None:
    """Handles contact sharing."""
    await update.message.reply_text("Phone number saved. Thank you!")

async def chat(update: Update, context: CallbackContext) -> None:
    """Handles user messages, applies sentiment analysis, and uses Gemini AI for response."""
    user_input = update.message.text.lower()

    # Detect if the user is saying goodbye
    farewell_keywords = ["bye", "goodbye", "see you", "take care", "later"]
    if any(word in user_input for word in farewell_keywords):
        sentiment_result = sentiment_pipeline(user_input)[0]
        sentiment_category = sentiment_result['label']
        sentiment_score = round(sentiment_result['score'], 2)

        if sentiment_category == "POSITIVE":
            farewell_response = "Goodbye! Have a fantastic day! 😊"
        elif sentiment_category == "NEGATIVE":
            farewell_response = "I'm here if you ever need to talk. Take care! 💙"
        else:
            farewell_response = "Take care! See you soon! 👋"

        await update.message.reply_text(f"Sentiment: {sentiment_category} ({sentiment_score})\n{farewell_response}")
        return  # Stop further processing

    # Regular chat handling
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

    sentiment_result = sentiment_pipeline(user_input)[0]
    sentiment_category = sentiment_result['label']
    sentiment_score = round(sentiment_result['score'], 2)

    await update.message.reply_text(f"Sentiment: {sentiment_category} ({sentiment_score})\n{bot_response}")

async def web_search(update: Update, context: CallbackContext) -> None:
    """Handles web search using Brave Search API."""
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
    """Handles file uploads (documents and images)."""
    file = update.message.document or (update.message.photo[-1] if update.message.photo else None)

    if file:
        file_id = file.file_id
        file_name = file.file_name if update.message.document else f"photo_{file_id}.jpg"

        try:
            file_path = await context.bot.get_file(file_id)
            await file_path.download_to_drive(file_name)
            await update.message.reply_text(f"File received: {file_name}")
        except Exception as e:
            logger.error(f"File Handling Error: {e}")
            await update.message.reply_text("Error processing the file.")

async def main() -> None:
    """Main function to set up and start the bot."""
    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.add_handler(CommandHandler("websearch", web_search))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, file_handler))

    logger.info("Bot is running...")

    await app.run_polling()

# Start the bot
try:
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
except RuntimeError as e:
    if "This event loop is already running" in str(e):
        logger.info("Event loop already running. Running bot in existing loop.")
        asyncio.ensure_future(main())
    else:
        raise
import logging
from services.sentiment import sentiment_pipeline
from services.gemini import call_gemini
from handlers.menu import get_main_menu

logger = logging.getLogger(__name__)

async def chat(update, context):
    text = update.message.text

    # ---------- MENU ROUTING (NEW) ----------
    if text == "💬 Gemini Chat":
        await update.message.reply_text(
            "💬 Gemini Chat mode enabled.\n\nSend me any message and I’ll respond using Gemini AI.",
            reply_markup=get_main_menu()
        )
        return

    if text == "🔍 Web Search":
        await update.message.reply_text(
            "🔍 Web Search mode.\n\nUse:\n/websearch <your query>",
            reply_markup=get_main_menu()
        )
        return

    if text == "📁 Upload File":
        await update.message.reply_text(
            "📁 File Upload mode.\n\nPlease upload a file or image now.",
            reply_markup=get_main_menu()
        )
        return

    # ---------- NORMAL CHAT FLOW ----------
    user_input = text.lower()

    # Farewell detection (UNCHANGED)
    farewell_keywords = ["bye", "goodbye", "see you", "take care", "later"]
    if any(word in user_input for word in farewell_keywords):
        sentiment_result = sentiment_pipeline(user_input)[0]
        category = sentiment_result["label"]
        score = round(sentiment_result["score"], 2)

        if category == "POSITIVE":
            response = "Goodbye! Have a fantastic day! 😊"
        elif category == "NEGATIVE":
            response = "I'm here if you ever need to talk. Take care! 💙"
        else:
            response = "Take care! See you soon! 👋"

        await update.message.reply_text(
            f"Sentiment: {category} ({score})\n{response}",
            reply_markup=get_main_menu()
        )
        return

    # Gemini response (UNCHANGED)
    try:
        bot_response = call_gemini(user_input)
    except Exception as e:
        logger.error(f"Gemini API Error: {e}")
        bot_response = "Sorry, there was an issue generating a response."

    # Sentiment analysis (UNCHANGED)
    sentiment_result = sentiment_pipeline(user_input)[0]
    category = sentiment_result["label"]
    score = round(sentiment_result["score"], 2)

    await update.message.reply_text(
        f"Sentiment: {category} ({score})\n{bot_response}",
        reply_markup=get_main_menu()
    )


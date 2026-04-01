import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from config import BOT_TOKEN
from handlers.start import start, contact_handler
from handlers.chat import chat
from handlers.websearch import web_search
from handlers.file_handler import file_handler

logging.basicConfig(level=logging.INFO)

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.CONTACT, contact_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    app.add_handler(CommandHandler("websearch", web_search))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, file_handler))

    app.run_polling()

if __name__ == "__main__":
    main()

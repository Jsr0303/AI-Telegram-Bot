from telegram import KeyboardButton, ReplyKeyboardMarkup
from handlers.menu import get_main_menu

async def start(update, context):
    reply_markup = ReplyKeyboardMarkup(
        [[KeyboardButton("Share Phone Number", request_contact=True)]],
        resize_keyboard=True
    )

    await update.message.reply_text(
        "Welcome!\nPlease share your phone number:",
        reply_markup=reply_markup
    )

    await update.message.reply_text(
        "Choose an option from the menu below 👇",
        reply_markup=get_main_menu()
    )

async def contact_handler(update, context):
    # Keeping original behavior (no DB change)
    await update.message.reply_text(
        "Phone number saved. Thank you!",
        reply_markup=get_main_menu()
    )

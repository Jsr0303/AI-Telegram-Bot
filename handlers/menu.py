from telegram import ReplyKeyboardMarkup

def get_main_menu():
    keyboard = [
        ["💬 Gemini Chat", "🔍 Web Search"],
        ["📁 Upload File"]
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )

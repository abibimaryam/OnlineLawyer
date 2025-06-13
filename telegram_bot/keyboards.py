from telegram import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="/help")],
            [KeyboardButton(text="/register"), KeyboardButton(text="/login"), KeyboardButton(text="/logout")],
            [KeyboardButton(text="/request")],
            [KeyboardButton(text="/cancel"), KeyboardButton(text="/start")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

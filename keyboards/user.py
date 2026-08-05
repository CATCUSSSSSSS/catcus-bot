from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def user_keyboard(mode):
    if mode == "anonymous":
        button = "🔄 Switch to Public"
    else:
        button = "🔄 Switch to Anonymous"

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=button)
            ]
        ],
        resize_keyboard=True
    )

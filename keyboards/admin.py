from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_panel():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 Broadcast",
                    callback_data="broadcast"
                ),
                InlineKeyboardButton(
                    text="👥 Users",
                    callback_data="users"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Statistics",
                    callback_data="stats"
                ),
                InlineKeyboardButton(
                    text="🚫 Ban List",
                    callback_data="ban_list"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✏️ Welcome Message",
                    callback_data="welcome"
                ),
                InlineKeyboardButton(
                    text="ℹ️ About Message",
                    callback_data="about"
                )
            ]
        ]
    )

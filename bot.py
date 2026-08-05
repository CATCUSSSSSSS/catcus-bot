import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.filters import Command

from config import BOT_TOKEN, ADMIN_ID
from database import (
    init_db,
    add_user,
    get_user_mode,
    change_mode,
    is_banned
)


bot = Bot(
    token=BOT_TOKEN,
    parse_mode=ParseMode.HTML
)

dp = Dispatcher()


def mode_keyboard(mode):
    if mode == "anonymous":
        text = "🔄 Switch to Public"
    else:
        text = "🔄 Switch to Anonymous"

    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=text)]
        ],
        resize_keyboard=True
    )


@dp.message(Command("start"))
async def start(message: types.Message):
    await add_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name
    )

    mode = await get_user_mode(message.from_user.id)

    await message.answer(
        "Welcome 👋\n\nSend your message.",
        reply_markup=mode_keyboard(mode)
    )


@dp.message(lambda m: m.text in [
    "🔄 Switch to Public",
    "🔄 Switch to Anonymous"
])
async def switch_mode(message: types.Message):

    current = await get_user_mode(message.from_user.id)

    new_mode = "public" if current == "anonymous" else "anonymous"

    await change_mode(
        message.from_user.id,
        new_mode
    )

    await message.answer(
        f"Mode changed to: {'👤 Public' if new_mode == 'public' else '🎭 Anonymous'}",
        reply_markup=mode_keyboard(new_mode)
    )


@dp.message()
async def receive_message(message: types.Message):

    if message.from_user.id == ADMIN_ID:
        return

    if await is_banned(message.from_user.id):
        return

    await add_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name
    )

    mode = await get_user_mode(message.from_user.id)

    if mode == "anonymous":
        header = "🎭 Anonymous"
    else:
        header = (
            f"👤 Public\n"
            f"Name: {message.from_user.full_name}\n"
            f"Username: @{message.from_user.username}"
        )

    await bot.send_message(
        ADMIN_ID,
        f"📩 New Message\n\n{header}"
    )

    await message.copy_to(
        ADMIN_ID
    )


async def main():
    await init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

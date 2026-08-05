import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup
)

from config import BOT_TOKEN, ADMIN_ID
from database import (
    init_db,
    add_user,
    get_user_mode,
    change_mode,
    is_banned,
    save_message,
    get_users_count
)

from texts import WELCOME_TEXT


bot = Bot(
    token=BOT_TOKEN,
    parse_mode=ParseMode.HTML
)

dp = Dispatcher()


reply_targets = {}


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
                    text="❌ Close",
                    callback_data="close"
                )
            ]
        ]
    )


def message_actions(user_id):

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💬 Reply",
                    callback_data=f"reply:{user_id}"
                ),
                InlineKeyboardButton(
                    text="🚫 Ban",
                    callback_data=f"ban:{user_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Delete",
                    callback_data="delete"
                )
            ]
        ]
    )


@dp.message(Command("start"))
async def start(message: types.Message):

    await add_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name
    )

    mode = await get_user_mode(
        message.from_user.id
    )

    await message.answer(
        WELCOME_TEXT,
        reply_markup=user_keyboard(mode)
    )


@dp.message(lambda m: m.text in [
    "🔄 Switch to Public",
    "🔄 Switch to Anonymous"
])
async def switch_mode(message: types.Message):

    current = await get_user_mode(
        message.from_user.id
    )

    new_mode = (
        "public"
        if current == "anonymous"
        else "anonymous"
    )

    await change_mode(
        message.from_user.id,
        new_mode
    )

    await message.answer(
        "Mode changed.",
        reply_markup=user_keyboard(new_mode)
    )
    @dp.message()
async def receive_message(message: types.Message):

    user_id = message.from_user.id

    if user_id == ADMIN_ID:
        return

    if await is_banned(user_id):
        return

    await add_user(
        user_id,
        message.from_user.username,
        message.from_user.full_name
    )

    mode = await get_user_mode(user_id)

    if mode == "anonymous":

        info = (
            "🎭 Anonymous\n"
            f"ID: {user_id}"
        )

    else:

        info = (
            "👤 Public\n"
            f"Name: {message.from_user.full_name}\n"
            f"Username: @{message.from_user.username}"
        )


    admin_message = await bot.send_message(
        ADMIN_ID,
        f"📩 New Message\n\n{info}",
        reply_markup=message_actions(user_id)
    )


    await message.copy_to(
        ADMIN_ID
    )


    await save_message(
        user_id,
        admin_message.message_id,
        mode
    )


@dp.callback_query(lambda c: c.data.startswith("reply:"))
async def reply_button(callback: types.CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        return

    user_id = int(
        callback.data.split(":")[1]
    )

    reply_targets[ADMIN_ID] = user_id

    await callback.message.answer(
        "💬 Send your reply now."
    )

    await callback.answer()


@dp.message(lambda m: m.from_user.id == ADMIN_ID)
async def admin_reply(message: types.Message):

    if ADMIN_ID not in reply_targets:
        return

    user_id = reply_targets[ADMIN_ID]

    try:

        await bot.send_message(
            user_id,
            "📨 Reply:\n\n" + message.text
        )

        await message.answer(
            "✅ Sent."
        )

    except:

        await message.answer(
            "❌ Failed to send."
        )


    del reply_targets[ADMIN_ID]


@dp.callback_query(lambda c: c.data.startswith("ban:"))
async def ban_button(callback: types.CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        return

    user_id = int(
        callback.data.split(":")[1]
    )

    from database import ban_user

    await ban_user(user_id)

    await callback.message.answer(
        "🚫 User banned."
    )

    await callback.answer()


@dp.callback_query(lambda c: c.data == "delete")
async def delete_button(callback: types.CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        return

    await callback.message.delete()

    await callback.answer()
    @dp.message(Command("admin"))
async def admin_command(message: types.Message):

    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "⚙️ Admin Panel",
        reply_markup=admin_panel()
    )


@dp.callback_query(lambda c: c.data == "stats")
async def stats_button(callback: types.CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        return

    count = await get_users_count()

    await callback.message.answer(
        f"📊 Statistics\n\n👥 Users: {count}"
    )

    await callback.answer()


@dp.callback_query(lambda c: c.data == "users")
async def users_button(callback: types.CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        return

    count = await get_users_count()

    await callback.message.answer(
        f"👥 Total users: {count}"
    )

    await callback.answer()


@dp.callback_query(lambda c: c.data == "broadcast")
async def broadcast_button(callback: types.CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        return

    await callback.message.answer(
        "📢 Broadcast mode is ready for upgrade."
    )

    await callback.answer()


@dp.callback_query(lambda c: c.data == "ban_list")
async def ban_list_button(callback: types.CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        return

    await callback.message.answer(
        "🚫 Ban management ready."
    )

    await callback.answer()


@dp.callback_query(lambda c: c.data == "close")
async def close_button(callback: types.CallbackQuery):

    if callback.from_user.id != ADMIN_ID:
        return

    await callback.message.delete()

    await callback.answer()


async def main():

    await init_db()

    print("Catcus Bot Started")

    await dp.start_polling(bot)


if __name__ == "__main__":

    asyncio.run(main())

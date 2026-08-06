import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from config import BOT_TOKEN, ADMIN_ID
from database import (
    init_db,
    add_user,
    get_user_mode,
    change_mode,
    is_banned,
    ban_user,
    save_message,
    get_users_count,
)
from texts import WELCOME_TEXT

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()

reply_targets = {}


def user_keyboard(mode):
    text = "🔄 Switch to Public" if mode == "anonymous" else "🔄 Switch to Anonymous"
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=text)]],
        resize_keyboard=True,
    )


def admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📢 Broadcast"), KeyboardButton(text="👥 Users")],
            [KeyboardButton(text="📊 Statistics"), KeyboardButton(text="🚫 Ban List")],
        ],
        resize_keyboard=True,
    )


def message_actions(user_id):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💬 Reply", callback_data=f"reply:{user_id}"),
                InlineKeyboardButton(text="🚫 Ban", callback_data=f"ban:{user_id}"),
            ],
            [InlineKeyboardButton(text="🗑 Delete", callback_data="delete")],
        ]
    )


@dp.message(Command("start"))
async def start(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("⚙️ Admin Panel", reply_markup=admin_keyboard())
        return

    await add_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name,
    )
    mode = await get_user_mode(message.from_user.id)
    await message.answer(WELCOME_TEXT, reply_markup=user_keyboard(mode))


@dp.message(lambda m: m.text in ["🔄 Switch to Public", "🔄 Switch to Anonymous"])
async def switch_mode(message: types.Message):
    current = await get_user_mode(message.from_user.id)
    new_mode = "public" if current == "anonymous" else "anonymous"
    await change_mode(message.from_user.id, new_mode)
    await message.answer("Mode changed.", reply_markup=user_keyboard(new_mode))


# --- Admin's persistent keyboard buttons ---
# Registered before admin_reply() on purpose: admin_reply's filter matches
# any non-command text from the admin, so if it came first it would swallow
# these button taps as if they were reply messages.

@dp.message(lambda m: m.from_user.id == ADMIN_ID and m.text == "📊 Statistics")
async def admin_stats(message: types.Message):
    count = await get_users_count()
    await message.answer(f"📊 Statistics\n\n👥 Users: {count}")


@dp.message(lambda m: m.from_user.id == ADMIN_ID and m.text == "👥 Users")
async def admin_users(message: types.Message):
    count = await get_users_count()
    await message.answer(f"👥 Total Users: {count}")


@dp.message(lambda m: m.from_user.id == ADMIN_ID and m.text == "📢 Broadcast")
async def admin_broadcast(message: types.Message):
    await message.answer("📢 Broadcast feature will be added.")


@dp.message(lambda m: m.from_user.id == ADMIN_ID and m.text == "🚫 Ban List")
async def admin_ban_list(message: types.Message):
    await message.answer("🚫 Ban list feature will be added.")


# This filter must exclude the admin. aiogram tries handlers in registration
# order and stops at the first match, so without this exclusion this catch-all
# handler grabs every admin message too (before admin_reply ever sees it),
# which is what was silently breaking the reply feature.
@dp.message(lambda m: m.from_user.id != ADMIN_ID)
async def receive_message(message: types.Message):
    user_id = message.from_user.id

    if await is_banned(user_id):
        return

    await add_user(
        user_id,
        message.from_user.username,
        message.from_user.full_name,
    )

    mode = await get_user_mode(user_id)

    if mode == "anonymous":
        info = f"🎭 Anonymous\nID: {user_id}"
    else:
        username = (
            f"@{message.from_user.username}"
            if message.from_user.username
            else "no username"
        )
        info = (
            "👤 Public\n"
            f"Name: {message.from_user.full_name}\n"
            f"Username: {username}"
        )

    header = f"📩 New Message\n\n{info}"

    if message.text:
        # Plain text: header + the message itself, as a single message.
        sent = await bot.send_message(
            ADMIN_ID,
            f"{header}\n\n{message.text}",
            reply_markup=message_actions(user_id),
        )
    else:
        # Media (photo, voice, document...): put the header in the caption so
        # it still arrives as one message. Some types (stickers, locations,
        # polls) don't support captions at all, and very long captions can be
        # rejected too — fall back to two messages only if that happens.
        caption = header
        if message.caption:
            caption += f"\n\n{message.caption}"
        try:
            sent = await message.copy_to(
                ADMIN_ID,
                caption=caption,
                reply_markup=message_actions(user_id),
            )
        except TelegramAPIError:
            sent = await bot.send_message(
                ADMIN_ID,
                header,
                reply_markup=message_actions(user_id),
            )
            await message.copy_to(ADMIN_ID)

    await save_message(user_id, sent.message_id, mode)


@dp.callback_query(lambda c: c.data.startswith("reply:"))
async def reply_button(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    user_id = int(callback.data.split(":")[1])
    reply_targets[ADMIN_ID] = user_id
    await callback.message.answer("💬 Send your reply now.")
    await callback.answer()


# `m.text and` guards against non-text messages (photo, sticker, voice...)
# from the admin — without it, m.text.startswith("/") crashes on None.
@dp.message(
    lambda m: m.from_user.id == ADMIN_ID and m.text and not m.text.startswith("/")
)
async def admin_reply(message: types.Message):
    if ADMIN_ID not in reply_targets:
        return

    user_id = reply_targets[ADMIN_ID]

    try:
        await bot.send_message(user_id, "📨 Reply:\n\n" + message.text)
        await message.answer("✅ Sent.")
    except TelegramAPIError:
        await message.answer(
            "⚠️ Couldn't deliver the reply — the user may have blocked the bot."
        )

    del reply_targets[ADMIN_ID]


@dp.callback_query(lambda c: c.data.startswith("ban:"))
async def ban_button(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    user_id = int(callback.data.split(":")[1])
    await ban_user(user_id)
    await callback.message.answer("🚫 User banned.")
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
    await message.answer("⚙️ Admin Panel", reply_markup=admin_keyboard())


async def main():
    await init_db()
    print("Catcus Bot Started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
                               

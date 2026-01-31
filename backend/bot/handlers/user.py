"""
User handlers for basic bot commands.
"""
import os
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from ..keyboards import get_main_menu_keyboard
from ..utils import is_admin

router = Router()

WEBAPP_URL = os.getenv("WEBAPP_URL", "https://yourdomain.com")


@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command."""
    user = message.from_user
    is_user_admin = is_admin(user.id)
    
    welcome_text = (
        f"👋 Добро пожаловать, <b>{user.first_name}</b>!\n\n"
        f"🛍 Это магазин. Нажмите кнопку ниже, чтобы открыть каталог товаров.\n\n"
        f"📦 Вы также можете посмотреть историю своих заказов."
    )
    
    if is_user_admin:
        welcome_text += "\n\n👨‍💼 <i>У вас есть права администратора.</i>"
    
    # Create Mini App button
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🛍 Открыть магазин",
        web_app=WebAppInfo(url=WEBAPP_URL)
    )
    
    await message.answer(
        welcome_text,
        reply_markup=builder.as_markup()
    )
    
    # Also send reply keyboard
    await message.answer(
        "Используйте меню ниже для навигации:",
        reply_markup=get_main_menu_keyboard(is_user_admin)
    )


@router.message(Command("get_my_id"))
async def cmd_get_my_id(message: Message):
    """Handle /get_my_id command - shows user's Telegram ID."""
    await message.answer(
        f"🆔 Ваш Telegram ID: <code>{message.from_user.id}</code>\n\n"
        f"Скопируйте этот ID и отправьте администратору, "
        f"чтобы он добавил вас в список админов."
    )


@router.message(F.text == "🛍 Открыть магазин")
async def open_shop(message: Message):
    """Open the Mini App."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🛍 Открыть каталог",
        web_app=WebAppInfo(url=WEBAPP_URL)
    )
    
    await message.answer(
        "Нажмите кнопку ниже, чтобы открыть магазин:",
        reply_markup=builder.as_markup()
    )


@router.message(F.text == "📦 Мои заказы")
async def my_orders(message: Message):
    """Show user's orders."""
    from ..utils import api_request
    
    result = await api_request(
        "GET",
        "/api/orders/me",
        params={"telegram_user_id": message.from_user.id}
    )
    
    if "error" in result:
        await message.answer("❌ Ошибка загрузки заказов. Попробуйте позже.")
        return
    
    orders = result.get("orders", [])
    
    if not orders:
        await message.answer(
            "📦 У вас пока нет заказов.\n\n"
            "Откройте магазин и добавьте товары в корзину!"
        )
        return
    
    text = f"📦 <b>Ваши заказы:</b>\n\n"
    
    status_emoji = {
        "new": "🆕",
        "accepted": "✅",
        "rejected": "❌",
        "completed": "📦"
    }
    
    for order in orders[:10]:  # Show last 10 orders
        status = order.get("status", "new")
        emoji = status_emoji.get(status, "📝")
        total = order.get("total_amount", 0)
        date = order.get("created_at", "")[:10]
        
        text += f"{emoji} Заказ #{order['id']} — {total}₽ ({date})\n"
    
    if len(orders) > 10:
        text += f"\n<i>...и ещё {len(orders) - 10} заказов</i>"
    
    await message.answer(text)


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command."""
    is_user_admin = is_admin(message.from_user.id)
    
    text = (
        "📋 <b>Доступные команды:</b>\n\n"
        "/start — Главное меню\n"
        "/get_my_id — Узнать свой Telegram ID\n"
        "/help — Показать эту справку\n"
    )
    
    if is_user_admin:
        text += (
            "\n<b>Команды администратора:</b>\n"
            "/admin — Открыть админ-панель\n"
            "/find [запрос] — Найти товар\n"
        )
    
    await message.answer(text)

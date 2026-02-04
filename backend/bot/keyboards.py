"""
Keyboard builders for Telegram bot.
"""
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def get_main_menu_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Main menu keyboard."""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="🛍 Открыть магазин"))
    builder.row(KeyboardButton(text="📦 Мои заказы"))
    
    if is_admin:
        builder.row(KeyboardButton(text="👨‍💼 Админ-панель"))
    
    return builder.as_markup(resize_keyboard=True)


def get_admin_menu_keyboard() -> InlineKeyboardMarkup:
    """Admin panel main menu."""
    builder = InlineKeyboardBuilder()
    
    # New Web Admin Panel
    from aiogram.types import WebAppInfo
    import os
    web_app_url = f"{os.getenv('WEBAPP_URL')}/admin.html"
    
    builder.row(
        InlineKeyboardButton(text="🌐 Открыть WEB Админ-панель", web_app=WebAppInfo(url=web_app_url))
    )
    
    builder.row(
        InlineKeyboardButton(text="➕ Добавить товар (Бот)", callback_data="admin:add_product")
    )
    builder.row(
        InlineKeyboardButton(text="🔍 Найти товар", callback_data="admin:find_product")
    )
    builder.row(
        InlineKeyboardButton(text="📁 Управление категориями", callback_data="admin:categories")
    )
    builder.row(
        InlineKeyboardButton(text="📦 Новые заказы", callback_data="admin:new_orders"),
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin:stats")
    )
    builder.row(
        InlineKeyboardButton(text="📉 Импорт из Excel", callback_data="admin:import_excel")
    )
    return builder.as_markup()


def get_categories_keyboard(categories: list, action: str = "select") -> InlineKeyboardMarkup:
    """Keyboard with category buttons."""
    builder = InlineKeyboardBuilder()
    
    for cat in categories:
        builder.row(
            InlineKeyboardButton(
                text=cat["name"],
                callback_data=f"cat:{action}:{cat['id']}"
            )
        )
    
    if action == "select":
        builder.row(
            InlineKeyboardButton(text="➕ Создать новую", callback_data="cat:create")
        )
    
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin:menu")
    )
    
    return builder.as_markup()


def get_subcategories_keyboard(subcategories: list, category_id: int, action: str = "select") -> InlineKeyboardMarkup:
    """Keyboard with subcategory buttons."""
    builder = InlineKeyboardBuilder()
    
    for subcat in subcategories:
        builder.row(
            InlineKeyboardButton(
                text=subcat["name"],
                callback_data=f"subcat:{action}:{subcat['id']}"
            )
        )
    
    if action == "select":
        builder.row(
            InlineKeyboardButton(text="➕ Создать новую", callback_data=f"subcat:create:{category_id}")
        )
    
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin:categories")
    )
    
    return builder.as_markup()


def get_category_management_keyboard() -> InlineKeyboardMarkup:
    """Category management menu."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📋 Список категорий", callback_data="cat:list")
    )
    builder.row(
        InlineKeyboardButton(text="➕ Создать категорию", callback_data="cat:create")
    )
    builder.row(
        InlineKeyboardButton(text="➕ Создать подкатегорию", callback_data="subcat:create_select")
    )
    builder.row(
        InlineKeyboardButton(text="✏️ Переименовать", callback_data="cat:rename_select")
    )
    builder.row(
        InlineKeyboardButton(text="🗑 Удалить категорию", callback_data="cat:delete_select")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin:menu")
    )
    return builder.as_markup()


def get_category_actions_keyboard(category_id: int) -> InlineKeyboardMarkup:
    """Actions for a single category."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📦 Товары", callback_data=f"cat:products:{category_id}")
    )
    builder.row(
        InlineKeyboardButton(text="➕ Добавить товар", callback_data=f"product:add_to:{category_id}")
    )
    builder.row(
        InlineKeyboardButton(text="✏️ Переименовать", callback_data=f"cat:rename:{category_id}"),
        InlineKeyboardButton(text="🗑 Удалить", callback_data=f"cat:delete:{category_id}")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="cat:list")
    )
    return builder.as_markup()


def get_product_actions_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """Actions for a single product."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✏️ Изменить", callback_data=f"product:edit:{product_id}"),
        InlineKeyboardButton(text="🗑 Удалить", callback_data=f"product:delete:{product_id}")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin:menu")
    )
    return builder.as_markup()


def get_product_edit_keyboard(product_id: int) -> InlineKeyboardMarkup:
    """What to edit in a product."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💰 Цена", callback_data=f"edit:price:{product_id}"),
        InlineKeyboardButton(text="📦 Остаток", callback_data=f"edit:stock:{product_id}")
    )
    builder.row(
        InlineKeyboardButton(text="📝 Название", callback_data=f"edit:name:{product_id}"),
        InlineKeyboardButton(text="📷 Фото", callback_data=f"edit:photo:{product_id}")
    )
    builder.row(
        InlineKeyboardButton(text="📁 Категория", callback_data=f"edit:category:{product_id}"),
        InlineKeyboardButton(text="📦 Шт. в пачке", callback_data=f"edit:pack:{product_id}")
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data=f"product:view:{product_id}")
    )
    return builder.as_markup()


def get_order_actions_keyboard(order_id: int, telegram_user_id: int) -> InlineKeyboardMarkup:
    """Actions for an order."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Принять", callback_data=f"order:accept:{order_id}"),
        InlineKeyboardButton(text="❌ Отклонить", callback_data=f"order:reject:{order_id}")
    )
    builder.row(
        InlineKeyboardButton(text="💬 Написать клиенту", url=f"tg://user?id={telegram_user_id}")
    )
    return builder.as_markup()


def get_skip_keyboard() -> InlineKeyboardMarkup:
    """Skip button."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="⏭ Пропустить", callback_data="skip")
    )
    return builder.as_markup()



def get_done_keyboard() -> InlineKeyboardMarkup:
    """Done or Cancel."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Готово", callback_data="done"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )
    return builder.as_markup()


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Cancel button."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )
    return builder.as_markup()


def get_confirm_keyboard(action: str, item_id: int) -> InlineKeyboardMarkup:
    """Confirm/cancel action."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"confirm:{action}:{item_id}"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
    )
    return builder.as_markup()


def remove_keyboard() -> ReplyKeyboardRemove:
    """Remove reply keyboard."""
    return ReplyKeyboardRemove()

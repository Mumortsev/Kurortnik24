"""
Telegram Admin Bot - Main entry point
Uses aiogram 3.x for Telegram Bot API
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .handlers import user, admin
from .handlers.admin import setup_admin_handlers

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set!")


async def main():
    """Initialize and start the bot."""
    # Initialize bot with default properties
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Initialize dispatcher
    dp = Dispatcher()
    
    # Include routers
    dp.include_router(user.router)
    dp.include_router(admin.router)
    
    # Setup admin handlers with FSM
    setup_admin_handlers(dp)
    
    print("Telegram Shop Bot started!")
    print("Press Ctrl+C to stop")
    
    # Start polling
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped")

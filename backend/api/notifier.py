"""
Notification utility to send messages to Telegram admins.
"""
import os
import asyncio
from typing import List
from dotenv import load_dotenv
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

async def notify_new_order(order_data: dict, items: List[dict]):
    """
    Send notification about new order to all admins.
    """
    if not BOT_TOKEN or not ADMIN_IDS:
        print("Warning: BOT_TOKEN or ADMIN_IDS not set. Notification skipped.")
        return

    try:
        # Initialize bot (session is created automatically)
        async with Bot(
            token=BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        ) as bot:
            
            # Format message
            items_text = ""
            for item in items:
                items_text += (
                    f"• {item['product_name']}: {item['quantity_packs']} пач "
                    f"({item['quantity_pieces']} шт) = {item['subtotal']}₽\n"
                )

            org = order_data.get("customer_organization")
            org_text = f"\n🏢 {org}" if org else ""
            
            message = (
                f"🆕 <b>Новый заказ #{order_data.get('id')}</b>\n"
                f"👤 {order_data.get('customer_name')}{org_text}\n"
                f"📱 {order_data.get('customer_phone')}\n\n"
                f"<b>Товары:</b>\n{items_text}\n"
                f"<b>💰 Итого: {order_data.get('total_amount')}₽</b>"
            )

            # Send to all admins
            for admin_id in ADMIN_IDS:
                try:
                    await bot.send_message(chat_id=admin_id, text=message)
                except Exception as e:
                    print(f"Failed to send to admin {admin_id}: {e}")
                    
    except Exception as e:
        print(f"Error sending notification: {e}")

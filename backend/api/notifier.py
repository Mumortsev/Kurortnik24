"""
Notification utility to send messages to Telegram admins.
Refactored to use httpx instead of aiogram to avoid dependency issues in API.
"""
import os
import httpx
import logging
from typing import List
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
# Parse ADMIN_IDS safely
try:
    ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
except ValueError:
    print("Error parsing ADMIN_IDS")
    ADMIN_IDS = []

async def notify_new_order(order_data: dict, items: List[dict]):
    """
    Send notification about new order to all admins using raw Telegram API.
    This avoids threading/event loop issues with aiogram in BackgroundTasks.
    """
    if not BOT_TOKEN or not ADMIN_IDS:
        print("Warning: BOT_TOKEN or ADMIN_IDS not set. Notification skipped.")
        return

    # Format message
    items_text = ""
    for item in items:
        # Escape HTML special chars if needed, but basic replacement is usually enough for these fields
        p_name = str(item['product_name']).replace("<", "&lt;").replace(">", "&gt;")
        items_text += (
            f"• {p_name}: {item['quantity_packs']} пач "
            f"({item['quantity_pieces']} шт) = {item['subtotal']}₽\n"
        )

    org = order_data.get("customer_organization")
    org_text = f"\n🏢 {org}" if org else ""
    
    # Safe getters
    c_name = str(order_data.get('customer_name', 'Unknown')).replace("<", "&lt;")
    
    message = (
        f"🆕 <b>Новый заказ #{order_data.get('id')}</b>\n"
        f"👤 {c_name}{org_text}\n"
        f"📱 {order_data.get('customer_phone')}\n\n"
        f"<b>Товары:</b>\n{items_text}\n"
        f"<b>💰 Итого: {order_data.get('total_amount')}₽</b>"
    )

    api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    async with httpx.AsyncClient(timeout=10.0) as client:
        for admin_id in ADMIN_IDS:
            try:
                payload = {
                    "chat_id": admin_id,
                    "text": message,
                    "parse_mode": "HTML"
                }
                response = await client.post(api_url, json=payload)
                if response.status_code != 200:
                    print(f"Failed to send to admin {admin_id}: {response.text}")
            except Exception as e:
                print(f"Error sending notification to {admin_id}: {e}")

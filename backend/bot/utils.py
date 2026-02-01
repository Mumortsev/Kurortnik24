"""
Utility functions for the Telegram bot.
"""
import os
import httpx
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]


def is_admin(user_id: int) -> bool:
    """Check if user is an admin."""
    return user_id in ADMIN_IDS


async def api_request(
    method: str,
    endpoint: str,
    data: Optional[Dict] = None,
    params: Optional[Dict] = None
) -> Dict[str, Any]:
    """Make a request to the API."""
    url = f"{API_URL}{endpoint}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        if method == "GET":
            response = await client.get(url, params=params)
        elif method == "POST":
            response = await client.post(url, json=data)
        elif method == "PUT":
            response = await client.put(url, json=data, params=params)
        elif method == "DELETE":
            response = await client.delete(url, params=params)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        if response.status_code >= 400:
            return {"error": True, "status": response.status_code, "detail": response.json().get("detail", "Error")}
        
        return response.json()


async def get_categories() -> List[Dict]:
    """Get all categories from API."""
    result = await api_request("GET", "/api/categories")
    if "error" in result:
        return []
    return result.get("categories", [])


async def get_products(
    category: Optional[int] = None,
    subcategory: Optional[int] = None,
    q: Optional[str] = None,
    page: int = 1,
    limit: int = 10
) -> Dict:
    """Get products from API."""
    params = {"page": page, "limit": limit}
    if category:
        params["category"] = category
    if subcategory:
        params["subcategory"] = subcategory
    if q:
        params["q"] = q
    
    return await api_request("GET", "/api/products", params=params)


async def get_product(product_id: int) -> Dict:
    """Get single product from API."""
    return await api_request("GET", f"/api/products/{product_id}")


async def create_product(data: Dict) -> Dict:
    """Create a new product."""
    return await api_request("POST", "/api/products", data=data)


async def update_product(product_id: int, data: Dict) -> Dict:
    """Update a product."""
    return await api_request("PUT", f"/api/products/{product_id}", data=data)


async def delete_product(product_id: int) -> Dict:
    """Delete a product."""
    return await api_request("DELETE", f"/api/products/{product_id}")


async def create_category(name: str) -> Dict:
    """Create a new category."""
    return await api_request("POST", "/api/categories", data={"name": name, "order": 0})


async def update_category(category_id: int, data: Dict) -> Dict:
    """Update a category."""
    return await api_request("PUT", f"/api/categories/{category_id}", data=data)


async def create_subcategory(category_id: int, name: str) -> Dict:
    """Create a new subcategory."""
    return await api_request(
        "POST",
        f"/api/categories/{category_id}/subcategories",
        data={"name": name, "order": 0, "category_id": category_id}
    )


async def delete_category(category_id: int) -> Dict:
    """Delete a category."""
    return await api_request("DELETE", f"/api/categories/{category_id}")


async def get_orders(status: Optional[str] = None) -> Dict:
    """Get orders from API."""
    params = {}
    if status:
        params["status"] = status
    return await api_request("GET", "/api/orders", params=params)


async def update_order_status(order_id: int, status: str) -> Dict:
    """Update order status."""
    return await api_request("PUT", f"/api/orders/{order_id}/status", params={"status": status})


def format_product_info(product: Dict) -> str:
    """Format product info for display."""
    pieces = product.get("pieces_per_pack", 1)
    price = product.get("price_per_unit", 0)
    stock = product.get("in_stock")
    stock_text = f"{stock} пачек" if stock is not None else "неограничено"
    
    return (
        f"<b>{product.get('name', 'Без названия')}</b>\n"
        f"💰 Цена: {price}₽ за шт\n"
        f"📦 В пачке: {pieces} шт\n"
        f"📊 Остаток: {stock_text}\n"
        f"🆔 ID: #{product.get('id', '?')}"
    )


def format_order_info(order: Dict) -> str:
    """Format order info for display."""
    items_text = ""
    for item in order.get("items", []):
        items_text += (
            f"• {item['product_name']}: {item['quantity_packs']} пачек "
            f"({item['quantity_pieces']} шт) = {item['subtotal']}₽\n"
        )
    
    org = order.get("customer_organization")
    org_text = f"\nОрганизация: {org}" if org else ""
    
    return (
        f"🛒 <b>Заказ #{order.get('id')}</b>\n"
        f"От: {order.get('customer_name')}{org_text}\n"
        f"Телефон: {order.get('customer_phone')}\n"
        f"User ID: {order.get('telegram_user_id')}\n\n"
        f"<b>Товары:</b>\n{items_text}\n"
        f"<b>Итого: {order.get('total_amount')}₽</b>\n"
        f"Статус: {order.get('status')}"
    )

"""
Script to import products from Tilda website.
Parses the page and extracts product information.
"""
import asyncio
import re
import sys
import os
from datetime import datetime
from urllib.parse import urljoin

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import httpx
    from bs4 import BeautifulSoup
except ImportError:
    print("Installing required packages...")
    os.system("pip install httpx beautifulsoup4 lxml")
    import httpx
    from bs4 import BeautifulSoup

# Configure
TILDA_URL = "https://project20913226.tilda.ws/"
LOG_FILE = "import_log.txt"


def log(message: str):
    """Log message to console and file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


async def fetch_page(url: str) -> str:
    """Fetch HTML content of a page."""
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        response.raise_for_status()
        return response.text


def extract_product_links(html: str, base_url: str) -> list:
    """Extract product page links from the catalog."""
    soup = BeautifulSoup(html, "lxml")
    links = []
    
    # Look for product links (Tilda uses various patterns)
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/tproduct/" in href or "product" in href.lower():
            full_url = urljoin(base_url, href)
            if full_url not in links:
                links.append(full_url)
    
    # Also look for product cards
    for card in soup.find_all(class_=re.compile(r"t-store__card|product|item")):
        link = card.find("a", href=True)
        if link:
            full_url = urljoin(base_url, link["href"])
            if full_url not in links:
                links.append(full_url)
    
    return links


def extract_product_data(html: str, url: str) -> dict:
    """Extract product data from product page."""
    soup = BeautifulSoup(html, "lxml")
    
    product = {
        "url": url,
        "name": None,
        "description": None,
        "price": None,
        "images": [],
        "category": None
    }
    
    # Try to find product name
    name_selectors = [
        "h1",
        ".t-store__prod-popup__name",
        ".t-store__card__title",
        '[data-product-name]',
        ".product-title",
        ".product-name"
    ]
    for selector in name_selectors:
        elem = soup.select_one(selector)
        if elem and elem.text.strip():
            product["name"] = elem.text.strip()
            break
    
    # Try to find price
    price_selectors = [
        ".t-store__prod-popup__price",
        ".t-store__card__price",
        '[data-product-price]',
        ".product-price",
        ".price"
    ]
    for selector in price_selectors:
        elem = soup.select_one(selector)
        if elem:
            text = elem.text.strip()
            # Extract number from price string
            numbers = re.findall(r"[\d\s]+", text.replace(" ", ""))
            if numbers:
                try:
                    product["price"] = float(numbers[0].strip())
                    break
                except ValueError:
                    pass
    
    # Try to find description
    desc_selectors = [
        ".t-store__prod-popup__descr",
        ".t-store__card__descr",
        ".product-description",
        ".description"
    ]
    for selector in desc_selectors:
        elem = soup.select_one(selector)
        if elem and elem.text.strip():
            product["description"] = elem.text.strip()[:1000]  # Limit length
            break
    
    # Try to find images
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-original")
        if src and ("product" in src.lower() or "tilda" in src.lower() or src.startswith("http")):
            if src.startswith("//"):
                src = "https:" + src
            if src not in product["images"]:
                product["images"].append(src)
    
    # Try to find category from breadcrumbs or navigation
    breadcrumb = soup.select_one(".breadcrumb, .t-menu__link-item--active")
    if breadcrumb:
        product["category"] = breadcrumb.text.strip()
    
    return product


async def get_categories_from_page(html: str) -> list:
    """Extract categories from navigation."""
    soup = BeautifulSoup(html, "lxml")
    categories = []
    
    # Look for navigation menu items
    for nav in soup.select(".t-menu__link-item, .t-menusub__link-item, nav a"):
        text = nav.text.strip()
        if text and len(text) < 50 and text.lower() not in ["главная", "home", "корзина", "cart", "контакты"]:
            if text not in categories:
                categories.append(text)
    
    return categories[:20]  # Limit to 20 categories


async def save_to_database(products: list, categories: list):
    """Save imported products to database via API."""
    import httpx
    
    API_URL = os.getenv("API_URL", "http://localhost:8000")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Create categories
        category_map = {}
        
        for cat_name in categories:
            try:
                response = await client.post(
                    f"{API_URL}/api/categories",
                    json={"name": cat_name, "order": 0}
                )
                if response.status_code == 200:
                    cat_data = response.json()
                    category_map[cat_name] = cat_data["id"]
                    log(f"✅ Создана категория: {cat_name}")
            except Exception as e:
                log(f"❌ Ошибка создания категории {cat_name}: {e}")
        
        # If no categories, create default
        if not category_map:
            try:
                response = await client.post(
                    f"{API_URL}/api/categories",
                    json={"name": "Товары", "order": 0}
                )
                if response.status_code == 200:
                    category_map["Товары"] = response.json()["id"]
            except:
                pass
        
        default_category_id = list(category_map.values())[0] if category_map else 1
        
        # Create products
        imported = 0
        failed = 0
        
        for product in products:
            if not product.get("name"):
                continue
            
            # Find category ID
            category_id = default_category_id
            if product.get("category") and product["category"] in category_map:
                category_id = category_map[product["category"]]
            
            product_data = {
                "name": product["name"],
                "description": product.get("description"),
                "price_per_unit": product.get("price") or 100,  # Default price if not found
                "pieces_per_pack": 1,  # Default, owner needs to update
                "min_order_packs": 1,
                "category_id": category_id,
                "image_url": product["images"][0] if product.get("images") else None,
                "active": True
            }
            
            try:
                response = await client.post(
                    f"{API_URL}/api/products",
                    json=product_data
                )
                if response.status_code == 200:
                    imported += 1
                    log(f"✅ Импортирован товар: {product['name']}")
                else:
                    failed += 1
                    log(f"❌ Ошибка импорта товара: {product['name']} - {response.text}")
            except Exception as e:
                failed += 1
                log(f"❌ Ошибка импорта товара: {product['name']} - {e}")
        
        return imported, failed


async def main():
    """Main import function."""
    log("=" * 50)
    log("Начало импорта из Tilda")
    log(f"URL: {TILDA_URL}")
    log("=" * 50)
    
    try:
        # Fetch main page
        log("Загрузка главной страницы...")
        html = await fetch_page(TILDA_URL)
        
        # Extract categories
        log("Извлечение категорий...")
        categories = await get_categories_from_page(html)
        log(f"Найдено категорий: {len(categories)}")
        for cat in categories:
            log(f"  - {cat}")
        
        # Extract product links
        log("Поиск товаров...")
        product_links = extract_product_links(html, TILDA_URL)
        log(f"Найдено ссылок на товары: {len(product_links)}")
        
        # If no product links found on main page, try to parse product cards directly
        products = []
        
        if product_links:
            # Fetch each product page
            for i, link in enumerate(product_links[:50], 1):  # Limit to 50 products
                log(f"Обработка товара {i}/{min(len(product_links), 50)}: {link}")
                try:
                    product_html = await fetch_page(link)
                    product_data = extract_product_data(product_html, link)
                    if product_data.get("name"):
                        products.append(product_data)
                        log(f"  ✓ {product_data['name']}")
                except Exception as e:
                    log(f"  ✗ Ошибка: {e}")
                
                # Small delay to be polite
                await asyncio.sleep(0.5)
        else:
            # Try to extract products directly from main page
            log("Попытка извлечь товары напрямую со страницы...")
            soup = BeautifulSoup(html, "lxml")
            
            for card in soup.select(".t-store__card, .product-card, [data-product-id]"):
                product = {
                    "name": None,
                    "price": None,
                    "images": []
                }
                
                # Name
                name_elem = card.select_one(".t-store__card__title, .product-name, h3, h4")
                if name_elem:
                    product["name"] = name_elem.text.strip()
                
                # Price
                price_elem = card.select_one(".t-store__card__price, .product-price, .price")
                if price_elem:
                    numbers = re.findall(r"[\d\s]+", price_elem.text.replace(" ", ""))
                    if numbers:
                        try:
                            product["price"] = float(numbers[0].strip())
                        except ValueError:
                            pass
                
                # Image
                img = card.select_one("img")
                if img:
                    src = img.get("src") or img.get("data-src")
                    if src:
                        if src.startswith("//"):
                            src = "https:" + src
                        product["images"].append(src)
                
                if product.get("name"):
                    products.append(product)
        
        log(f"\nВсего извлечено товаров: {len(products)}")
        
        if not products:
            log("\n⚠️ Товары не найдены. Возможные причины:")
            log("  - Сайт использует JavaScript для загрузки товаров")
            log("  - Структура страницы отличается от стандартной Tilda")
            log("  - Товары ещё не добавлены на сайт")
            log("\nРекомендация: добавьте товары вручную через админку бота")
            return
        
        # Save to database
        log("\nСохранение в базу данных...")
        imported, failed = await save_to_database(products, categories)
        
        log("\n" + "=" * 50)
        log(f"Импорт завершён!")
        log(f"  ✅ Успешно импортировано: {imported}")
        log(f"  ❌ Ошибок: {failed}")
        log("=" * 50)
        
        log("\n⚠️ ВАЖНО: Для каждого товара необходимо:")
        log("  1. Установить количество штук в пачке (pieces_per_pack)")
        log("  2. Распределить товары по подкатегориям")
        log("  3. Загрузить фото через Telegram-бота")
        
    except Exception as e:
        log(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🔄 Скрипт импорта товаров из Tilda\n")
    asyncio.run(main())

"""
Database initialization script.
Creates tables and optionally seeds demo data.
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from dotenv import load_dotenv
load_dotenv()

from api.database import init_db, AsyncSessionLocal
from api.models import Category, Subcategory, Product


async def create_demo_data():
    """Create demo categories and products."""
    async with AsyncSessionLocal() as session:
        # Check if data already exists
        from sqlalchemy import select
        result = await session.execute(select(Category))
        if result.scalars().first():
            print("⚠️ Данные уже существуют, пропускаем создание демо-данных")
            return
        
        print("📦 Создание демо-данных...")
        
        # Create categories
        categories_data = [
            {"name": "INTEX", "order": 1},
            {"name": "Надувка (Китай)", "order": 2},
            {"name": "Палатки и зонты", "order": 3},
            {"name": "Маски, очки и ласты", "order": 4},
            {"name": "Летняя обувь", "order": 5},
            {"name": "Аквашузы", "order": 6},
            {"name": "Сумки пляжные", "order": 7},
            {"name": "Лежаки", "order": 8},
            {"name": "Полотенца", "order": 9},
            {"name": "Расчески", "order": 10},
            {"name": "Полесье", "order": 11},
            {"name": "Игрушки", "order": 12},
            {"name": "Спорттовары и мячи", "order": 13},
            {"name": "Средства от комаров", "order": 14},
            {"name": "Средства для загара", "order": 15},
            {"name": "Сачки, чесалки и катаны", "order": 16},
            {"name": "Изделия из дерева", "order": 17},
            {"name": "Кружки", "order": 18},
            {"name": "Гипсовые статуэтки", "order": 19},
            {"name": "Мыло", "order": 20},
            {"name": "Ароматизаторы для автомобиля", "order": 21},
            {"name": "Шторки для авто", "order": 22},
            {"name": "Стулья", "order": 23},
            {"name": "Статуэтки из полистоуна", "order": 24},
            {"name": "Чайники", "order": 25},
            {"name": "Пемза", "order": 26},
            {"name": "Пепельницы", "order": 27},
            {"name": "Глицерин", "order": 28},
            {"name": "Ракушки", "order": 29},
            {"name": "Все для шашлыка", "order": 30},
            {"name": "Магниты", "order": 31},
            {"name": "Тарелки", "order": 32},
        ]
        
        categories = []
        for cat_data in categories_data:
            cat = Category(**cat_data)
            session.add(cat)
            categories.append(cat)
        
        await session.flush()
        
        # Create subcategories
        subcategories_data = []
        
        # Находим индексы категорий Магниты (31) и Тарелки (32)
        # В коде выше они добавляются в том же порядке
        magnets_cat_id = categories[30].id
        plates_cat_id = categories[31].id
        
        cities = ["Джубга", "Лермонтово", "Новомихайловское", "Архипо-Осиповка", "Геленджик", "Черное море"]
        
        for i, city in enumerate(cities):
            subcategories_data.append({"category_id": magnets_cat_id, "name": city, "order": i+1})
            subcategories_data.append({"category_id": plates_cat_id, "name": city, "order": i+1})
        
        subcategories = []
        for sub_data in subcategories_data:
            sub = Subcategory(**sub_data)
            session.add(sub)
            subcategories.append(sub)
        
        await session.flush()
        
        # Create demo products
        products_data = [
            {
                "name": "Саморез 3.5x16 жёлтый цинк",
                "description": "Универсальный саморез для дерева и ДСП. Потайная головка, крестовой шлиц.",
                "price_per_unit": 0.5,
                "pieces_per_pack": 100,
                "category_id": categories[0].id,
                "subcategory_id": subcategories[0].id,
                "in_stock": 50,
            },
            {
                "name": "Саморез 4.2x32 чёрный",
                "description": "Саморез по металлу с буром. Оксидированное покрытие.",
                "price_per_unit": 0.8,
                "pieces_per_pack": 50,
                "category_id": categories[0].id,
                "subcategory_id": subcategories[0].id,
                "in_stock": 100,
            },
            {
                "name": "Болт М8x40 DIN 933",
                "description": "Болт с шестигранной головкой, полная резьба. Класс прочности 8.8.",
                "price_per_unit": 5,
                "pieces_per_pack": 25,
                "category_id": categories[0].id,
                "subcategory_id": subcategories[1].id,
                "in_stock": 30,
            },
            {
                "name": "Гайка М8 DIN 934",
                "description": "Шестигранная гайка. Класс прочности 8.",
                "price_per_unit": 2,
                "pieces_per_pack": 50,
                "category_id": categories[0].id,
                "subcategory_id": subcategories[2].id,
                "in_stock": None,  # Unlimited
            },
            {
                "name": "Отвёртка крестовая PH2",
                "description": "Профессиональная отвёртка с намагниченным наконечником.",
                "price_per_unit": 150,
                "pieces_per_pack": 1,
                "category_id": categories[1].id,
                "subcategory_id": subcategories[4].id,
                "in_stock": 20,
            },
            {
                "name": "Перчатки х/б с ПВХ",
                "description": "Рабочие перчатки хлопчатобумажные с точечным покрытием.",
                "price_per_unit": 25,
                "pieces_per_pack": 12,
                "category_id": categories[2].id,
                "subcategory_id": subcategories[6].id,
                "in_stock": 100,
            },
        ]
        
        for product_data in products_data:
            product = Product(**product_data, active=True)
            session.add(product)
        
        await session.commit()
        print(f"✅ Создано {len(categories_data)} категорий, {len(subcategories_data)} подкатегорий, {len(products_data)} товаров")


async def main():
    """Initialize database."""
    print("🗄️ Инициализация базы данных...")
    
    # Create tables
    await init_db()
    print("✅ Таблицы созданы")
    
    # Ask about demo data
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        await create_demo_data()
    else:
        print("\n💡 Для создания демо-данных запустите:")
        print("   python init_db.py --demo")
    
    print("\n✅ База данных готова к работе!")


if __name__ == "__main__":
    asyncio.run(main())

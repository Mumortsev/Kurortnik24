import asyncio
import os
import sys

# Добавляем путь к бэкенду
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from api.database import AsyncSessionLocal, init_db
from api.models import Category, Subcategory, Product
from sqlalchemy import select, update, delete

NEW_CATEGORIES = [
    "INTEX", "Надувка (Китай)", "Палатки и зонты", "Маски, очки и ласты",
    "Летняя обувь", "Аквашузы", "Сумки пляжные", "Лежаки", "Полотенца",
    "Расчески", "Полесье", "Игрушки", "Спорттовары и мячи", "Средства от комаров",
    "Средства для загара", "Сачки, чесалки и катаны", "Изделия из дерева",
    "Кружки", "Гипсовые статуэтки", "Мыло", "Ароматизаторы для автомобиля",
    "Шторки для авто", "Стулья", "Статуэтки из полистоуна", "Чайники",
    "Пемза", "Пепельницы", "Глицерин", "Ракушки", "Все для шашлыка",
    "Магниты", "Тарелки"
]

CITIES = [
    "Джубга", "Лермонтово", "Новомихайловское", "Архипо-Осиповка", 
    "Геленджик", "Черное море"
]

# Маппинг старых имен (из имен файлов) на новые
MAPPING = {
    "Обувь": "Летняя обувь",
    "Зонты и палатки": "Палатки и зонты",
    "Катана  чесалка сачек": "Сачки, чесалки и катаны",
    "Маски Ласты": "Маски, очки и ласты"
}

async def reorganize():
    print("Starting category reorganization...")
    await init_db()
    
    async with AsyncSessionLocal() as session:
        # 1. Сначала сохраняем существующие товары и их старые категории
        result = await session.execute(select(Category))
        old_categories = result.scalars().all()
        old_cat_map = {cat.name: cat.id for cat in old_categories}
        print(f"Found old categories: {list(old_cat_map.keys())}")

        # 2. Создаем новые категории
        new_cat_objects = {}
        for i, name in enumerate(NEW_CATEGORIES):
            # Проверяем, существует ли уже такая категория
            result = await session.execute(select(Category).where(Category.name == name))
            cat = result.scalars().first()
            if not cat:
                cat = Category(name=name, order=i+1)
                session.add(cat)
                await session.flush()
                print(f"Created category: {name}")
            else:
                cat.order = i+1
                print(f"Updated order for: {name}")
            new_cat_objects[name] = cat

        # 3. Переносим товары из старых категорий в новые по маппингу
        for old_name, new_name in MAPPING.items():
            if old_name in old_cat_map and new_name in new_cat_objects:
                old_id = old_cat_map[old_name]
                new_id = new_cat_objects[new_name].id
                
                res = await session.execute(
                    update(Product)
                    .where(Product.category_id == old_id)
                    .values(category_id=new_id)
                )
                print(f"Moved products from '{old_name}' to '{new_name}': {res.rowcount}")

        # 4. Создаем подкатегории для Магнитов и Тарелок
        for cat_name in ["Магниты", "Тарелки"]:
            cat = new_cat_objects[cat_name]
            for i, city in enumerate(CITIES):
                result = await session.execute(
                    select(Subcategory).where(
                        Subcategory.category_id == cat.id,
                        Subcategory.name == city
                    )
                )
                if not result.scalars().first():
                    sub = Subcategory(category_id=cat.id, name=city, order=i+1)
                    session.add(sub)
                    print(f"Added subcategory '{city}' to '{cat_name}'")

        # 5. Удаляем пустые старые категории, которых нет в новом списке
        for old_name, old_id in old_cat_map.items():
            if old_name not in NEW_CATEGORIES and old_name not in MAPPING:
                # Проверяем, остались ли в ней товары
                result = await session.execute(select(Product).where(Product.category_id == old_id))
                if not result.scalars().first():
                    await session.execute(delete(Category).where(Category.id == old_id))
                    print(f"Deleted empty old category: {old_name}")

        await session.commit()
        print("Reorganization complete!")

if __name__ == "__main__":
    asyncio.run(reorganize())

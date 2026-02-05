import asyncio
import sys
import os

# Add the current directory to sys.path to ensure we can import 'api'
sys.path.append(os.getcwd())

from sqlalchemy import select
from api.database import AsyncSessionLocal, init_db
from api.models import Category, Subcategory

# Data to seed
# Data to seed - Sorted and Corrected
SIMPLE_CATEGORIES = [
    "INTEX",
    "Аквашузы",
    "Ароматизаторы для автомобиля",
    "Бижутерия",
    "Все для шашлыка",
    "Гипсовые статуэтки",
    "Глицерин",
    "Изделия из дерева",
    "Игрушки",
    "Кружки",
    "Лежаки",
    "Летняя обувь",
    "Маски, Очки, Ласты",
    "Мыло",
    "Надувка Китай",
    "Палатки, Зонты",
    "Пемза",
    "Пепельницы",
    "Полесье",
    "Полотенца",
    "Ракушки",
    "Расчески",
    "Сачки, Чесалки, Катаны",
    "Спорттовары, Мячи",
    "Средства для загара",
    "Средства от комаров",
    "Статуэтки из полистоуна",
    "Стулья",
    "Сумки",
    "Сумки пляжные",
    "Чайники",
    "Шторки для авто"
]

COMPLEX_CATEGORIES = {
    "Магниты": [
        "Архипо-Осиповка",
        "Геленджик",
        "Джубга",
        "Лермонтово",
        "Новомихайловское",
        "Черное море"
    ],
    "Тарелки": [
        "Архипо-Осиповка",
        "Геленджик",
        "Джубга",
        "Лермонтово",
        "Новомихайловское",
        "Черное море"
    ]
}

async def seed_categories():
    print("Beginning database seeding...")
    await init_db()
    
    async with AsyncSessionLocal() as session:
        # 1. Add Simple Categories
        for cat_name in SIMPLE_CATEGORIES:
            # Check if exists
            result = await session.execute(select(Category).where(Category.name == cat_name))
            if not result.scalars().first():
                new_cat = Category(name=cat_name)
                session.add(new_cat)
                print(f"Added category: {cat_name}")
            else:
                print(f"Category exists: {cat_name}")
        
        # 2. Add Complex Categories with Subcategories
        for cat_name, subcats in COMPLEX_CATEGORIES.items():
            # Check/Create Parent Category
            result = await session.execute(select(Category).where(Category.name == cat_name))
            parent_cat = result.scalars().first()
            
            if not parent_cat:
                parent_cat = Category(name=cat_name)
                session.add(parent_cat)
                await session.flush() # Flush to get ID
                print(f"Added parent category: {cat_name}")
            else:
                print(f"Parent category exists: {cat_name}")
            
            # Check/Create Subcategories
            for sub_name in subcats:
                res_sub = await session.execute(
                    select(Subcategory).where(
                        Subcategory.category_id == parent_cat.id,
                        Subcategory.name == sub_name
                    )
                )
                if not res_sub.scalars().first():
                    new_sub = Subcategory(category_id=parent_cat.id, name=sub_name)
                    session.add(new_sub)
                    print(f"  - Added subcategory: {sub_name}")
                else:
                    print(f"  - Subcategory exists: {sub_name}")

        await session.commit()
        print("Seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed_categories())

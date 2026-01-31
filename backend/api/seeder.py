from sqlalchemy import select
from .database import AsyncSessionLocal
from .models import Category, Subcategory
import logging

logger = logging.getLogger(__name__)

# Data to seed
SIMPLE_CATEGORIES = [
    "INTEX", "Надувка Китай", "Палатки-зонты", "Маски-Очки-Ласты", 
    "Летняя обувь", "Аквашузы", "Сумки пляжные", "Лежаки", "Полотенца", 
    "Расчески", "Полесье", "Игрушки", "Спортовары-мячи", "Средства от комаров", 
    "Средство для загара", "Сачки-чесалки-Катаны", "Изделья из дерева", "Кружки", 
    "Гипсовые статуэтки", "Бижутерия", "Мыло", "Ароматизатор для автомобиля", 
    "Шторка для Авто", "Стулья", "Статуэтки из полистоуна", "Чайники", "Пемза", 
    "Пепельница", "Глицерин", "Ракушки", "Все для шашлыка", "Водное оружие"
]

COMPLEX_CATEGORIES = {
    "Магниты": [
        "Джубга", "Лермонтово", "Новомихайловское", 
        "Архипо Осиповка", "Геленджик", "Черное море"
    ],
    "Тарелки": [
        "Джубга", "Лермонтово", "Новомихайловское", 
        "Архипо Осиповка", "Геленджик", "Черное море"
    ]
}

async def seed_categories():
    """Seed categories into the database if they don't exist."""
    logger.info("Checking/Seeding categories...")
    
    async with AsyncSessionLocal() as session:
        # 1. Add Simple Categories
        for cat_name in SIMPLE_CATEGORIES:
            result = await session.execute(select(Category).where(Category.name == cat_name))
            if not result.scalars().first():
                new_cat = Category(name=cat_name)
                session.add(new_cat)
                logger.info(f"Added category: {cat_name}")
        
        # 2. Add Complex Categories with Subcategories
        for cat_name, subcats in COMPLEX_CATEGORIES.items():
            # Check/Create Parent Category
            result = await session.execute(select(Category).where(Category.name == cat_name))
            parent_cat = result.scalars().first()
            
            if not parent_cat:
                parent_cat = Category(name=cat_name)
                session.add(parent_cat)
                await session.flush() # Flush to get ID
                logger.info(f"Added parent category: {cat_name}")
            
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
                    logger.info(f"  - Added subcategory: {sub_name}")

        await session.commit()
        logger.info("Category seeding complete.")

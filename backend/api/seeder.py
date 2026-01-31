from sqlalchemy import select
from .database import AsyncSessionLocal
from .models import Category, Subcategory, Product
import logging
import random

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

# Demo products template
DEMO_PRODUCTS = {
    "INTEX": ("Матрас надувной Royal", 1500, 5),
    "Надувка Китай": ("Круг детский 'Утенок'", 350, 10),
    "Палатки-зонты": ("Зонт пляжный 2м", 800, 1),
    "Маски-Очки-Ласты": ("Маска для плавания PRO", 1200, 1),
    "Летняя обувь": ("Сланцы пляжные", 450, 1),
    "Аквашузы": ("Аквашузы неопреновые", 600, 1),
    "Сумки пляжные": ("Сумка 'Морской бриз'", 900, 1),
    "Лежаки": ("Лежак складной", 2500, 1),
    "Полотенца": ("Полотенце махровое 70х140", 550, 1),
    "Расчески": ("Расческа массажная", 150, 12),
    "Полесье": ("Самосвал 'Мираж'", 850, 4),
    "Игрушки": ("Набор для песочницы", 300, 10),
    "Спортовары-мячи": ("Мяч волейбольный", 700, 1),
    "Средства от комаров": ("Спирали от комаров (10шт)", 120, 20),
    "Средство для загара": ("Масло для загара SPF 15", 350, 6),
    "Сачки-чесалки-Катаны": ("Сачок детский", 100, 20),
    "Изделья из дерева": ("Ложка деревянная расписная", 250, 10),
    "Кружки": ("Кружка сувенирная 'Море'", 300, 6),
    "Гипсовые статуэтки": ("Копилка 'Кот'", 400, 1),
    "Бижутерия": ("Браслет из ракушек", 150, 10),
    "Мыло": ("Мыло ручной работы 'Роза'", 200, 10),
    "Ароматизатор для автомобиля": ("Ароматизатор 'Океан'", 100, 20),
    "Шторка для Авто": ("Шторка солнцезащитная", 400, 1),
    "Стулья": ("Стул туристический складной", 1200, 1),
    "Статуэтки из полистоуна": ("Фигурка 'Дельфин'", 550, 1),
    "Чайники": ("Чайник походный 1.5л", 900, 1),
    "Пемза": ("Пемза натуральная", 80, 20),
    "Пепельница": ("Пепельница керамическая", 250, 6),
    "Глицерин": ("Глицерин косметический", 100, 10),
    "Ракушки": ("Набор ракушек 'Черное море'", 300, 1),
    "Все для шашлыка": ("Набор шампуров (6шт)", 800, 1),
    "Водное оружие": ("Водный пистолет SuperSoaker", 650, 6)
}

async def seed_categories():
    """Seed categories AND demo products into the database if they don't exist."""
    logger.info("Checking/Seeding categories and products...")
    
    async with AsyncSessionLocal() as session:
        # 1. Add Simple Categories and Products
        for cat_name in SIMPLE_CATEGORIES:
            # Check/Add Category
            result = await session.execute(select(Category).where(Category.name == cat_name))
            cat = result.scalars().first()
            if not cat:
                cat = Category(name=cat_name)
                session.add(cat)
                await session.flush()
                logger.info(f"Added category: {cat_name}")
            
            # Check/Add Product (only if category has no products)
            prod_result = await session.execute(select(Product).where(Product.category_id == cat.id))
            if not prod_result.scalars().first():
                demo_data = DEMO_PRODUCTS.get(cat_name, (f"Товар {cat_name}", 500, 1))
                new_prod = Product(
                    name=demo_data[0],
                    category_id=cat.id,
                    price_per_unit=demo_data[1],
                    pieces_per_pack=demo_data[2],
                    min_order_packs=1,
                    description=f"Отличный товар из категории {cat_name}. Высокое качество.",
                    active=True,
                    in_stock=100
                )
                session.add(new_prod)
                logger.info(f"  + Added demo product: {demo_data[0]}")

        # 2. Add Complex Categories with Subcategories and Products
        for cat_name, subcats in COMPLEX_CATEGORIES.items():
            # Check/Create Parent Category
            result = await session.execute(select(Category).where(Category.name == cat_name))
            parent_cat = result.scalars().first()
            
            if not parent_cat:
                parent_cat = Category(name=cat_name)
                session.add(parent_cat)
                await session.flush()
                logger.info(f"Added parent category: {cat_name}")
            
            # Check/Create Subcategories and Products
            for sub_name in subcats:
                res_sub = await session.execute(
                    select(Subcategory).where(
                        Subcategory.category_id == parent_cat.id,
                        Subcategory.name == sub_name
                    )
                )
                sub = res_sub.scalars().first()
                if not sub:
                    sub = Subcategory(category_id=parent_cat.id, name=sub_name)
                    session.add(sub)
                    await session.flush()
                    logger.info(f"  - Added subcategory: {sub_name}")
                
                # Check/Add Product to Subcategory
                prod_result = await session.execute(select(Product).where(Product.subcategory_id == sub.id))
                if not prod_result.scalars().first():
                    base_price = random.randint(100, 500)
                    new_prod = Product(
                        name=f"{cat_name} {sub_name} (Сувенир)",
                        category_id=parent_cat.id,
                        subcategory_id=sub.id,
                        price_per_unit=base_price,
                        pieces_per_pack=random.choice([1, 5, 10]),
                        min_order_packs=1,
                        description=f"Сувенирная продукция: {cat_name} с видом {sub_name}.",
                        active=True,
                        in_stock=100
                    )
                    session.add(new_prod)
                    logger.info(f"    + Added demo product: {new_prod.name}")

        await session.commit()
        logger.info("Category and product seeding complete.")

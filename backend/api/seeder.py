from sqlalchemy import select
from .database import AsyncSessionLocal
from .models import Category, Subcategory, Product
import logging
import random

logger = logging.getLogger(__name__)

# Data to seed
# Data to seed - Sorted and Corrected
# Data to seed - Sorted and Corrected
SIMPLE_CATEGORIES = [
    "INTEX",
    "Аквашузы",
    "Ароматизаторы для автомобиля",
    "Бижутерия",
    "Водное оружие",
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

# Demo products template
DEMO_PRODUCTS = {
    "INTEX": ("Матрас надувной 183х69см", 850, 6),
    "Аквашузы": ("Аквашузы взрослые, р. 36-45", 350, 1),
    "Ароматизаторы для автомобиля": ("Ароматизатор 'Новая машина'", 80, 20),
    "Бижутерия": ("Браслет на ногу с ракушкой", 120, 10),
    "Водное оружие": ("Водный бластер 40см", 450, 10),
    "Все для шашлыка": ("Решетка гриль глубокая", 650, 5),
    "Гипсовые статуэтки": ("Копилка 'Золотой тигр'", 350, 4),
    "Глицерин": ("Глицерин для рук 100мл", 100, 20),
    "Изделия из дерева": ("Лопатка кухонная бук", 150, 20),
    "Игрушки": ("Набор формочек 'Замок'", 200, 15),
    "Кружки": ("Кружка 'Лучший отпуск' 300мл", 250, 12),
    "Лежаки": ("Лежак пляжный складной", 1800, 2),
    "Летняя обувь": ("Сланцы 'Пляж' женские", 300, 10),
    "Маски, Очки, Ласты": ("Маска для ныряния с трубкой", 900, 5),
    "Мыло": ("Мыло сувенирное 'Морская звезда'", 150, 20),
    "Надувка Китай": ("Круг надувной 'Пончик' 90см", 400, 20),
    "Палатки, Зонты": ("Пляжный зонт 1.8м с наклоном", 1100, 5),
    "Пемза": ("Пемза натуральная вулканическая", 60, 30),
    "Пепельницы": ("Пепельница карманная 'Море'", 150, 20),
    "Полесье": ("Машина-каталка 'Джип'", 2100, 1),
    "Полотенца": ("Полотенце пляжное микрофибра", 700, 10),
    "Ракушки": ("Набор ракушек для декора", 250, 10),
    "Расчески": ("Расческа деревянная массажная", 180, 15),
    "Сачки, Чесалки, Катаны": ("Сачок для бабочек телескопический", 200, 20),
    "Спорттовары, Мячи": ("Мяч футбольный пляжный", 550, 10),
    "Средства для загара": ("Крем от загара SPF 50", 450, 10),
    "Средства от комаров": ("Спрей от комаров 'Тайга'", 180, 15),
    "Статуэтки из полистоуна": ("Фигурка садовая 'Гном'", 600, 4),
    "Стулья": ("Стул рыбацкий", 850, 5),
    "Сумки": ("Сумка шопер текстильная", 350, 20),
    "Сумки пляжные": ("Сумка пляжная большая прозрачная", 800, 5),
    "Чайники": ("Чайник эмалированный 2л", 1200, 3),
    "Шторки для авто": ("Комплект шторок на присосках", 300, 10)
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

import pandas as pd
from sqlalchemy import select
from api.database import AsyncSessionLocal
from api.models import Category, Subcategory, Product
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_excel_import(file_path: str):
    """
    Обработка Excel файла и импорт в БД.
    Колонки: Категория, Подкатегория, Наименование, Артикул, Цена (за 1 шт/₽), Кол-во в пачке (шт), Описание
    """
    try:
        df = pd.read_excel(file_path)
        # Очистка названий колонок от лишних пробелов
        df.columns = [c.strip() for c in df.columns]
        
        async with AsyncSessionLocal() as session:
            count_added = 0
            count_updated = 0
            
            for _, row in df.iterrows():
                cat_name = str(row.get('Категория', '')).strip()
                sub_name = str(row.get('Подкатегория', '')).strip()
                name = str(row.get('Наименование', '')).strip()
                article = str(row.get('Артикул', '')).strip()
                price = row.get('Цена (за 1 шт/₽)', 0)
                pack_size = row.get('Кол-во в пачке (шт)', 1)
                desc = str(row.get('Описание', '')).strip()
                
                if not name or name == 'nan':
                    continue
                
                # 1. Поиск категории
                res = await session.execute(select(Category).where(Category.name == cat_name))
                category = res.scalars().first()
                if not category:
                    category = Category(name=cat_name)
                    session.add(category)
                    await session.flush()
                
                # 2. Поиск подкатегории (если есть)
                subcategory_id = None
                if sub_name and sub_name != 'nan':
                    res = await session.execute(
                        select(Subcategory).where(
                            Subcategory.category_id == category.id,
                            Subcategory.name == sub_name
                        )
                    )
                    subcategory = res.scalars().first()
                    if not subcategory:
                        subcategory = Subcategory(category_id=category.id, name=sub_name)
                        session.add(subcategory)
                        await session.flush()
                    subcategory_id = subcategory.id
                
                # 3. Поиск и обновление/создание товара
                res = await session.execute(
                    select(Product).where(
                        Product.name == name,
                        Product.category_id == category.id
                    )
                )
                product = res.scalars().first()
                
                if product:
                    product.price_per_unit = price
                    product.pieces_per_pack = int(pack_size)
                    product.description = desc if desc != 'nan' else None
                    product.subcategory_id = subcategory_id
                    count_updated += 1
                else:
                    product = Product(
                        name=name,
                        category_id=category.id,
                        subcategory_id=subcategory_id,
                        price_per_unit=price,
                        pieces_per_pack=int(pack_size),
                        description=desc if desc != 'nan' else None,
                        active=True
                    )
                    session.add(product)
                    count_added += 1
            
            await session.commit()
            return f"✅ Импорт завершен!\nДобавлено: {count_added}\nОбновлено: {count_updated}"
            
    except Exception as e:
        logger.error(f"Excel import error: {e}")
        return f"❌ Ошибка при обработке файла: {str(e)}"

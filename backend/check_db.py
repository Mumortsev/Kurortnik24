import asyncio
import sys
import os

sys.path.append(os.getcwd())

from sqlalchemy import select
from api.database import AsyncSessionLocal
from api.models import Category, Subcategory

async def check_db():
    async with AsyncSessionLocal() as session:
        print("--- Categories ---")
        result = await session.execute(select(Category))
        categories = result.scalars().all()
        for c in categories:
            print(f"ID: {c.id}, Name: {c.name}")
            
        print("\n--- Subcategories ---")
        result = await session.execute(select(Subcategory))
        subcategories = result.scalars().all()
        for s in subcategories:
            print(f"ID: {s.id}, CatID: {s.category_id}, Name: {s.name}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check_db())

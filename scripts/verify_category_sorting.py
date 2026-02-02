import sys
import os
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Add project root to path
sys.path.append(os.getcwd())

# Ensure we use the correct DB path if running from root
if os.path.exists("backend/shop.db") and "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///backend/shop.db"
    print(f"Set DATABASE_URL to {os.environ['DATABASE_URL']}")

from backend.api.database import AsyncSessionLocal
from backend.api.models import Category

async def verify():
    print("Connecting to database...")
    async with AsyncSessionLocal() as db:
        print("Executing query...")
        # Simulating the API query
        result = await db.execute(
            select(Category)
            .options(selectinload(Category.subcategories))
            .order_by(Category.name)
        )
        categories = result.scalars().all()
        
        print("\n--- Categories (from DB with .order_by(Category.name)) ---")
        category_names = []
        for cat in categories:
            print(f"Category: {cat.name} (ID: {cat.id})")
            category_names.append(cat.name)
            
            # Simulate API subcategory sorting
            sorted_subs = sorted(cat.subcategories, key=lambda x: x.name)
            for sub in sorted_subs:
                print(f"  - Subcategory: {sub.name}")

        print("\n--- Verification Results ---")
        expected_names = sorted(category_names)
        if category_names == expected_names:
            print("[SUCCESS] Categories are sorted alphabetically.")
        else:
            print("[FAIL] Categories are NOT sorted alphabetically.")
            print(f"Expected: {expected_names}")
            print(f"Actual:   {category_names}")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify())

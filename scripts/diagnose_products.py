import sys
import os
import asyncio
import traceback
from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Add project root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.api.database import AsyncSessionLocal
from backend.api.models import Product

async def main():
    print("Connecting to DB...")
    async with AsyncSessionLocal() as session:
        try:
            print("Querying products with images...")
            stmt = select(Product).options(selectinload(Product.images)).limit(1)
            result = await session.execute(stmt)
            p = result.scalar_one_or_none()
            print("Query successful.")
            if p:
                print(f"Product ID: {p.id}")
                print(f"Images: {p.images}")
            else:
                print("No products found.")
        except Exception as e:
            print(f"ERROR: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())

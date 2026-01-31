import sys
import os
import asyncio
from sqlalchemy import select

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.api.database import engine, Base, AsyncSessionLocal
from backend.api.models import Product, ProductImage

async def migrate():
    print("Starting migration...")
    
    # 1. Create tables (specifically product_images)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created/verified.")
    
    # 2. Migrate existing data
    async with AsyncSessionLocal() as session:
        # Get all products
        result = await session.execute(select(Product))
        products = result.scalars().unique().all() # unique() important for relationships
        
        migrated_count = 0
        skipped_count = 0
        
        for p in products:
            # Refresh to load relationships
            # await session.refresh(p, attribute_names=["images"]) 
            # OR just check existing
            
            # Check if has images relation loaded or empty
            # Since we just added the relationship, access might trigger lazy load if session active
            # But let's check existing DB records
            existing_imgs_res = await session.execute(
                select(ProductImage).where(ProductImage.product_id == p.id)
            )
            existing_imgs = existing_imgs_res.scalars().all()
            
            if not existing_imgs and (p.image_file_id or p.image_url):
                print(f"Migrating images for Product #{p.id}...")
                img = ProductImage(
                    product_id=p.id,
                    file_id=p.image_file_id,
                    image_url=p.image_url,
                    is_main=True
                )
                session.add(img)
                migrated_count += 1
            else:
                skipped_count += 1
        
        await session.commit()
        print(f"Migration completed. Migrated: {migrated_count}, Skipped (already has images or no image): {skipped_count}")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(migrate())

"""
Products API routes with filtering, sorting, and pagination.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from sqlalchemy.orm import selectinload
from ..models import Product, ProductImage
from ..schemas import (
    ProductResponse, ProductCreate, ProductUpdate,
    ProductListResponse, MessageResponse
)

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=ProductListResponse)
async def get_products(
    category: Optional[int] = Query(None, description="Filter by category ID"),
    subcategory: Optional[int] = Query(None, description="Filter by subcategory ID"),
    q: Optional[str] = Query(None, description="Search by name"),
    sort: Optional[str] = Query("newest", description="Sort: price_asc, price_desc, name_asc, name_desc, newest, oldest"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get products with filtering, sorting, and pagination.
    """
    # Base query with eager loading of images
    query = select(Product).options(selectinload(Product.images)).where(Product.active == True)
    
    # Apply filters
    if category:
        query = query.where(Product.category_id == category)
    
    if subcategory:
        query = query.where(Product.subcategory_id == subcategory)
    
    if q:
        search_term = f"%{q}%"
        query = query.where(
            or_(
                Product.name.ilike(search_term),
                Product.description.ilike(search_term)
            )
        )
    
    # Apply sorting
    sort_mapping = {
        "price_asc": Product.price_per_unit.asc(),
        "price_desc": Product.price_per_unit.desc(),
        "name_asc": Product.name.asc(),
        "name_desc": Product.name.desc(),
        "newest": Product.created_at.desc(),
        "oldest": Product.created_at.asc(),
    }
    order_clause = sort_mapping.get(sort, Product.created_at.desc())
    query = query.order_by(order_clause)
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    
    # Execute
    result = await db.execute(query)
    products = result.scalars().all()
    
    # Calculate pages
    pages = (total + limit - 1) // limit if total > 0 else 1
    
    return ProductListResponse(
        items=products,
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single product by ID."""
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.images))
        .where(Product.id == product_id, Product.active == True)
    )
    product = result.scalar_one_or_none()
    
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    return product


@router.post("", response_model=ProductResponse)
async def create_product(
    product: ProductCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new product."""
    product_data = product.model_dump()
    images_ids = product_data.pop("images", []) or [] # Remove images from dict
    
    # Use first image as main for backward compatibility fields
    if images_ids:
        product_data["image_file_id"] = images_ids[0]

    db_product = Product(**product_data)
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    
    # Create images
    if images_ids:
        for idx, file_id in enumerate(images_ids):
            img = ProductImage(
                product_id=db_product.id,
                file_id=file_id,
                is_main=(idx == 0)
            )
            db.add(img)
        await db.commit()
        # Reload product with images
        result = await db.execute(
            select(Product).options(selectinload(Product.images)).where(Product.id == db_product.id)
        )
        db_product = result.scalar_one()

    return db_product


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product: ProductUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a product."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    db_product = result.scalar_one_or_none()
    
    if not db_product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    update_data = product.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product, key, value)
    
    await db.commit()
    await db.refresh(db_product)
    return db_product


@router.delete("/{product_id}", response_model=MessageResponse)
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db)):
    """Delete (deactivate) a product."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    db_product = result.scalar_one_or_none()
    
    if not db_product:
        raise HTTPException(status_code=404, detail="Товар не найден")
    
    # Soft delete - just deactivate
    db_product.active = False
    await db.commit()
    
    return MessageResponse(message="Товар удалён", id=product_id)

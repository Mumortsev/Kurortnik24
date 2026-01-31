"""
Categories API routes.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import Category, Subcategory
from ..schemas import (
    CategoryResponse, CategoryCreate, CategoryTreeResponse,
    SubcategoryResponse, SubcategoryCreate, MessageResponse
)

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=CategoryTreeResponse)
async def get_categories(db: AsyncSession = Depends(get_db)):
    """Get all categories with their subcategories."""
    result = await db.execute(
        select(Category)
        .options(selectinload(Category.subcategories))
        .order_by(Category.order, Category.id)
    )
    categories = result.scalars().all()
    
    # Sort subcategories by order
    for category in categories:
        category.subcategories = sorted(category.subcategories, key=lambda x: (x.order, x.id))
    
    return CategoryTreeResponse(categories=categories)


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single category by ID."""
    result = await db.execute(
        select(Category)
        .options(selectinload(Category.subcategories))
        .where(Category.id == category_id)
    )
    category = result.scalar_one_or_none()
    
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    
    return category


@router.post("", response_model=CategoryResponse)
async def create_category(
    category: CategoryCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new category."""
    db_category = Category(**category.model_dump())
    db.add(db_category)
    await db.commit()
    
    # Reload with relationships
    result = await db.execute(
        select(Category)
        .options(selectinload(Category.subcategories))
        .where(Category.id == db_category.id)
    )
    db_category = result.scalar_one()
    
    return db_category


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category: CategoryCreate,
    db: AsyncSession = Depends(get_db)
):
    """Update a category."""
    result = await db.execute(select(Category).where(Category.id == category_id))
    db_category = result.scalar_one_or_none()
    
    if not db_category:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    
    for key, value in category.model_dump().items():
        setattr(db_category, key, value)
    
    await db.commit()
    await db.refresh(db_category)
    return db_category


@router.delete("/{category_id}", response_model=MessageResponse)
async def delete_category(category_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a category."""
    result = await db.execute(
        select(Category)
        .options(selectinload(Category.products))
        .where(Category.id == category_id)
    )
    db_category = result.scalar_one_or_none()
    
    if not db_category:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    
    if db_category.products:
        raise HTTPException(
            status_code=400,
            detail=f"Нельзя удалить категорию: в ней {len(db_category.products)} товаров"
        )
    
    await db.delete(db_category)
    await db.commit()
    return MessageResponse(message="Категория удалена")


# --- Subcategory routes ---

@router.post("/{category_id}/subcategories", response_model=SubcategoryResponse)
async def create_subcategory(
    category_id: int,
    subcategory: SubcategoryCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new subcategory within a category."""
    # Check category exists
    result = await db.execute(select(Category).where(Category.id == category_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Категория не найдена")
    
    db_subcategory = Subcategory(category_id=category_id, **subcategory.model_dump(exclude={"category_id"}))
    db.add(db_subcategory)
    await db.commit()
    await db.refresh(db_subcategory)
    return db_subcategory


@router.put("/subcategories/{subcategory_id}", response_model=SubcategoryResponse)
async def update_subcategory(
    subcategory_id: int,
    subcategory: SubcategoryCreate,
    db: AsyncSession = Depends(get_db)
):
    """Update a subcategory."""
    result = await db.execute(select(Subcategory).where(Subcategory.id == subcategory_id))
    db_subcategory = result.scalar_one_or_none()
    
    if not db_subcategory:
        raise HTTPException(status_code=404, detail="Подкатегория не найдена")
    
    db_subcategory.name = subcategory.name
    db_subcategory.order = subcategory.order
    
    await db.commit()
    await db.refresh(db_subcategory)
    return db_subcategory


@router.delete("/subcategories/{subcategory_id}", response_model=MessageResponse)
async def delete_subcategory(subcategory_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a subcategory."""
    result = await db.execute(
        select(Subcategory)
        .options(selectinload(Subcategory.products))
        .where(Subcategory.id == subcategory_id)
    )
    db_subcategory = result.scalar_one_or_none()
    
    if not db_subcategory:
        raise HTTPException(status_code=404, detail="Подкатегория не найдена")
    
    if db_subcategory.products:
        raise HTTPException(
            status_code=400,
            detail=f"Нельзя удалить подкатегорию: в ней {len(db_subcategory.products)} товаров"
        )
    
    await db.delete(db_subcategory)
    await db.commit()
    return MessageResponse(message="Подкатегория удалена")

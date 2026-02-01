"""
Orders API routes with cart validation and order management.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models import Product, Order, OrderItem
from ..schemas import (
    CartValidateRequest, CartValidateResponse, CartValidateError,
    OrderCreate, OrderResponse, OrderListResponse, MessageResponse
)
# from ..notifier import notify_new_order

router = APIRouter(prefix="/api", tags=["orders"])


@router.post("/cart/validate", response_model=CartValidateResponse)
async def validate_cart(
    cart: CartValidateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Validate cart items before checkout.
    Checks if quantities are valid multiples of pack sizes and products are in stock.
    """
    errors = []
    total_amount = 0.0
    
    for item in cart.items:
        result = await db.execute(
            select(Product).where(Product.id == item.product_id, Product.active == True)
        )
        product = result.scalar_one_or_none()
        
        if not product:
            errors.append(CartValidateError(
                product_id=item.product_id,
                product_name="Неизвестный товар",
                error="Товар не найден или недоступен"
            ))
            continue
        
        # Check minimum order
        if item.quantity_packs < product.min_order_packs:
            errors.append(CartValidateError(
                product_id=product.id,
                product_name=product.name,
                error=f"Минимальный заказ: {product.min_order_packs} пачек"
            ))
            continue
        
        # Check stock
        if product.in_stock is not None and item.quantity_packs > product.in_stock:
            errors.append(CartValidateError(
                product_id=product.id,
                product_name=product.name,
                error=f"Недостаточно товара. Доступно: {product.in_stock} пачек"
            ))
            continue
        
        # Calculate subtotal
        pieces = item.quantity_packs * product.pieces_per_pack
        subtotal = pieces * float(product.price_per_unit)
        total_amount += subtotal
    
    return CartValidateResponse(
        valid=len(errors) == 0,
        errors=errors,
        total_amount=round(total_amount, 2)
    )


@router.post("/orders", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new order.
    Validates all items and calculates totals.
    """
    # Validate cart first
    cart_request = CartValidateRequest(
        items=[{"product_id": item.product_id, "quantity_packs": item.quantity_packs} for item in order_data.items]
    )
    validation = await validate_cart(cart_request, db)
    
    if not validation.valid:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Ошибка валидации корзины",
                "errors": [e.model_dump() for e in validation.errors]
            }
        )
    
    # Create order
    db_order = Order(
        telegram_user_id=order_data.telegram_user_id,
        customer_name=order_data.customer_name,
        customer_organization=order_data.customer_organization,
        customer_phone=order_data.customer_phone,
        total_amount=validation.total_amount,
        status="new"
    )
    db.add(db_order)
    await db.flush()  # Get order ID
    
    # Create order items
    for item in order_data.items:
        result = await db.execute(select(Product).where(Product.id == item.product_id))
        product = result.scalar_one()
        
        pieces = item.quantity_packs * product.pieces_per_pack
        subtotal = pieces * float(product.price_per_unit)
        
        db_item = OrderItem(
            order_id=db_order.id,
            product_id=product.id,
            quantity_packs=item.quantity_packs,
            quantity_pieces=pieces,
            price_per_unit=float(product.price_per_unit),
            subtotal=subtotal
        )
        db.add(db_item)
        
        # Update stock if tracked
        if product.in_stock is not None:
            product.in_stock -= item.quantity_packs
    
    await db.commit()
    
    # Fetch complete order with items
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == db_order.id)
    )
    order = result.scalar_one()
    
    # Build response with product names
    order_response = OrderResponse(
        id=order.id,
        telegram_user_id=order.telegram_user_id,
        customer_name=order.customer_name,
        customer_organization=order.customer_organization,
        customer_phone=order.customer_phone,
        total_amount=float(order.total_amount),
        status=order.status,
        created_at=order.created_at,
        items=[]
    )
    
    items_data = []
    for item in order.items:
        product_result = await db.execute(select(Product).where(Product.id == item.product_id))
        product = product_result.scalar_one()
        item_dict = {
            "id": item.id,
            "product_id": item.product_id,
            "product_name": product.name,
            "quantity_packs": item.quantity_packs,
            "quantity_pieces": item.quantity_pieces,
            "price_per_unit": float(item.price_per_unit),
            "subtotal": float(item.subtotal)
        }
        order_response.items.append(item_dict)
        items_data.append(item_dict)
        
    # Send notification in background
    # order_info = {
    #     "id": order.id,
    #     "customer_name": order.customer_name,
    #     "customer_organization": order.customer_organization,
    #     "customer_phone": order.customer_phone,
    #     "total_amount": float(order.total_amount)
    # }
    # background_tasks.add_task(notify_new_order, order_info, items_data)
    
    return order_response


@router.get("/orders/me", response_model=OrderListResponse)
async def get_my_orders(
    telegram_user_id: int = Query(..., description="Telegram user ID"),
    db: AsyncSession = Depends(get_db)
):
    """Get orders for a specific Telegram user."""
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.telegram_user_id == telegram_user_id)
        .order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()
    
    order_responses = []
    for order in orders:
        order_resp = OrderResponse(
            id=order.id,
            telegram_user_id=order.telegram_user_id,
            customer_name=order.customer_name,
            customer_organization=order.customer_organization,
            customer_phone=order.customer_phone,
            total_amount=float(order.total_amount),
            status=order.status,
            created_at=order.created_at,
            items=[]
        )
        
        for item in order.items:
            product_result = await db.execute(select(Product).where(Product.id == item.product_id))
            product = product_result.scalar_one_or_none()
            order_resp.items.append({
                "id": item.id,
                "product_id": item.product_id,
                "product_name": product.name if product else "Удалённый товар",
                "quantity_packs": item.quantity_packs,
                "quantity_pieces": item.quantity_pieces,
                "price_per_unit": float(item.price_per_unit),
                "subtotal": float(item.subtotal)
            })
        
        order_responses.append(order_resp)
    
    return OrderListResponse(orders=order_responses)


@router.put("/orders/{order_id}/status", response_model=MessageResponse)
async def update_order_status(
    order_id: int,
    status: str = Query(..., description="New status: new, accepted, rejected, completed"),
    db: AsyncSession = Depends(get_db)
):
    """Update order status (admin only)."""
    valid_statuses = ["new", "accepted", "rejected", "completed"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Неверный статус. Допустимые: {', '.join(valid_statuses)}")
    
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    order.status = status
    await db.commit()
    
    return MessageResponse(message=f"Статус заказа #{order_id} изменён на '{status}'")


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single order by ID."""
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
    
    order_resp = OrderResponse(
        id=order.id,
        telegram_user_id=order.telegram_user_id,
        customer_name=order.customer_name,
        customer_organization=order.customer_organization,
        customer_phone=order.customer_phone,
        total_amount=float(order.total_amount),
        status=order.status,
        created_at=order.created_at,
        items=[]
    )
    
    for item in order.items:
        product_result = await db.execute(select(Product).where(Product.id == item.product_id))
        product = product_result.scalar_one_or_none()
        order_resp.items.append({
            "id": item.id,
            "product_id": item.product_id,
            "product_name": product.name if product else "Удалённый товар",
            "quantity_packs": item.quantity_packs,
            "quantity_pieces": item.quantity_pieces,
            "price_per_unit": float(item.price_per_unit),
            "subtotal": float(item.subtotal)
        })
    
    return order_resp


@router.get("/orders", response_model=OrderListResponse)
async def get_all_orders(
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db)
):
    """Get all orders (admin only)."""
    query = select(Order).options(selectinload(Order.items)).order_by(Order.created_at.desc())
    
    if status:
        query = query.where(Order.status == status)
    
    result = await db.execute(query)
    orders = result.scalars().all()
    
    order_responses = []
    for order in orders:
        order_resp = OrderResponse(
            id=order.id,
            telegram_user_id=order.telegram_user_id,
            customer_name=order.customer_name,
            customer_organization=order.customer_organization,
            customer_phone=order.customer_phone,
            total_amount=float(order.total_amount),
            status=order.status,
            created_at=order.created_at,
            items=[]
        )
        
        for item in order.items:
            product_result = await db.execute(select(Product).where(Product.id == item.product_id))
            product = product_result.scalar_one_or_none()
            order_resp.items.append({
                "id": item.id,
                "product_id": item.product_id,
                "product_name": product.name if product else "Удалённый товар",
                "quantity_packs": item.quantity_packs,
                "quantity_pieces": item.quantity_pieces,
                "price_per_unit": float(item.price_per_unit),
                "subtotal": float(item.subtotal)
            })
        
        order_responses.append(order_resp)
    
    return OrderListResponse(orders=order_responses)

"""
SQLAlchemy ORM models for the shop database.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, Integer, Numeric, Boolean, ForeignKey, DateTime, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class Category(Base):
    """Product category model."""
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    subcategories: Mapped[List["Subcategory"]] = relationship(
        "Subcategory", back_populates="category", cascade="all, delete-orphan"
    )
    products: Mapped[List["Product"]] = relationship(
        "Product", back_populates="category"
    )

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"


class Subcategory(Base):
    """Product subcategory model."""
    __tablename__ = "subcategories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    category: Mapped["Category"] = relationship("Category", back_populates="subcategories")
    products: Mapped[List["Product"]] = relationship("Product", back_populates="subcategory")

    def __repr__(self):
        return f"<Subcategory(id={self.id}, name='{self.name}')>"




class ProductImage(Base):
    """Product additional images model."""
    __tablename__ = "product_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    
    file_id: Mapped[str] = mapped_column(String(255), nullable=True)  # Telegram file_id
    image_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True) # External URL
    
    is_main: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="images")

    def __repr__(self):
        return f"<ProductImage(id={self.id}, product={self.product_id})>"


class Product(Base):
    """Product model with wholesale logic."""
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id"), nullable=False)
    subcategory_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("subcategories.id"), nullable=True)
    
    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Pricing and wholesale logic
    price_per_unit: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    pieces_per_pack: Mapped[int] = mapped_column(Integer, default=1)
    min_order_packs: Mapped[int] = mapped_column(Integer, default=1)
    
    # Images (Deprecated single image fields, kept for backward compatibility)
    image_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    image_file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Stock and status
    in_stock: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # None = unlimited
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    category: Mapped["Category"] = relationship("Category", back_populates="products")
    subcategory: Mapped[Optional["Subcategory"]] = relationship("Subcategory", back_populates="products")
    order_items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="product")
    images: Mapped[List["ProductImage"]] = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', price={self.price_per_unit})>"


class Order(Base):
    """Customer order model."""
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_organization: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    customer_phone: Mapped[str] = mapped_column(String(50), nullable=False)
    
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="new")  # new, accepted, rejected, completed
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Order(id={self.id}, user={self.telegram_user_id}, total={self.total_amount})>"


class OrderItem(Base):
    """Order item model (line item in an order)."""
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), nullable=False)
    
    quantity_packs: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity_pieces: Mapped[int] = mapped_column(Integer, nullable=False)
    price_per_unit: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="items")
    product: Mapped["Product"] = relationship("Product", back_populates="order_items")

    def __repr__(self):
        return f"<OrderItem(order={self.order_id}, product={self.product_id}, packs={self.quantity_packs})>"

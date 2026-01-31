"""
Pydantic schemas for API request/response validation.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# --- Category Schemas ---

class SubcategoryBase(BaseModel):
    name: str
    order: int = 0


class SubcategoryCreate(SubcategoryBase):
    category_id: int


class SubcategoryResponse(SubcategoryBase):
    id: int
    category_id: int

    class Config:
        from_attributes = True


class CategoryBase(BaseModel):
    name: str
    order: int = 0


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int
    subcategories: List[SubcategoryResponse] = []

    class Config:
        from_attributes = True


class CategoryTreeResponse(BaseModel):
    """Full category tree with subcategories."""
    categories: List[CategoryResponse]


# --- Product Schemas ---

class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price_per_unit: float = Field(..., gt=0)
    pieces_per_pack: int = Field(default=1, ge=1)
    min_order_packs: int = Field(default=1, ge=1)
    image_url: Optional[str] = None
    image_file_id: Optional[str] = None
    in_stock: Optional[int] = None  # None = unlimited
    active: bool = True


class ProductCreate(ProductBase):
    category_id: int
    subcategory_id: Optional[int] = None
    images: Optional[List[str]] = None  # List of file_ids


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price_per_unit: Optional[float] = Field(default=None, gt=0)
    pieces_per_pack: Optional[int] = Field(default=None, ge=1)
    min_order_packs: Optional[int] = Field(default=None, ge=1)
    category_id: Optional[int] = None
    subcategory_id: Optional[int] = None
    image_url: Optional[str] = None
    image_file_id: Optional[str] = None
    in_stock: Optional[int] = None
    active: Optional[bool] = None



class ProductImageResponse(BaseModel):
    id: int
    file_id: Optional[str]
    image_url: Optional[str]
    is_main: bool

    class Config:
        from_attributes = True


class ProductResponse(ProductBase):
    id: int
    category_id: int
    subcategory_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    images: List[ProductImageResponse] = []

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Paginated product list response."""
    items: List[ProductResponse]
    total: int
    page: int
    limit: int
    pages: int


# --- Cart Schemas ---

class CartItem(BaseModel):
    product_id: int
    quantity_packs: int = Field(..., ge=1)


class CartValidateRequest(BaseModel):
    items: List[CartItem]


class CartValidateError(BaseModel):
    product_id: int
    product_name: str
    error: str


class CartValidateResponse(BaseModel):
    valid: bool
    errors: List[CartValidateError] = []
    total_amount: float = 0


# --- Order Schemas ---

class OrderItemCreate(BaseModel):
    product_id: int
    quantity_packs: int = Field(..., ge=1)


class OrderCreate(BaseModel):
    customer_name: str = Field(..., min_length=1)
    customer_organization: Optional[str] = None
    customer_phone: str = Field(..., min_length=5)
    items: List[OrderItemCreate]
    telegram_user_id: int


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity_packs: int
    quantity_pieces: int
    price_per_unit: float
    subtotal: float

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    telegram_user_id: int
    customer_name: str
    customer_organization: Optional[str] = None
    customer_phone: str
    total_amount: float
    status: str
    created_at: datetime
    items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    orders: List[OrderResponse]


# --- Admin Schemas ---

class AdminAuth(BaseModel):
    telegram_user_id: int


class MessageResponse(BaseModel):
    message: str
    id: Optional[int] = None

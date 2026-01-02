"""
Pydantic schemas for wishlist items
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class WishlistItemBase(BaseModel):
    """Base wishlist item schema with common fields"""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    image_url: Optional[str] = Field(None, max_length=500)  # Optional
    product_url: Optional[str] = Field(None, max_length=500)  # Optional - users can add items without URL


class WishlistItemCreate(WishlistItemBase):
    """Schema for creating a wishlist item"""
    pass


class WishlistItemUpdate(BaseModel):
    """Schema for updating a wishlist item (all fields optional)"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    image_url: Optional[str] = Field(None, min_length=1, max_length=500)
    product_url: Optional[str] = Field(None, min_length=1, max_length=500)


class WishlistItem(WishlistItemBase):
    """Complete wishlist item schema"""
    id: str
    is_purchased: bool = False
    purchased_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MarkAsPurchasedDTO(BaseModel):
    """Schema for marking an item as purchased"""
    purchased_by: str = Field(..., min_length=1, max_length=100)

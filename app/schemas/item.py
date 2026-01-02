"""
Pydantic schemas for wishlist items
"""
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field, HttpUrl


class ContributionBase(BaseModel):
    """Base contribution schema"""
    contributor_name: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., gt=0)  # Amount must be positive
    message: Optional[str] = Field(None, max_length=500)


class ContributionCreate(ContributionBase):
    """Schema for creating a contribution"""
    pass


class Contribution(ContributionBase):
    """Complete contribution schema"""
    id: str
    item_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class WishlistItemBase(BaseModel):
    """Base wishlist item schema with common fields"""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    image_url: Optional[str] = Field(None, max_length=500)  # Optional
    product_url: Optional[str] = Field(None, max_length=500)  # Optional - users can add items without URL

    # Pooled gift fields
    item_type: Literal["normal", "pooled_gift"] = "normal"
    target_amount: Optional[float] = Field(None, gt=0)  # Required if item_type is pooled_gift


class WishlistItemCreate(WishlistItemBase):
    """Schema for creating a wishlist item"""
    pass


class WishlistItemUpdate(BaseModel):
    """Schema for updating a wishlist item (all fields optional)"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    image_url: Optional[str] = Field(None, min_length=1, max_length=500)
    product_url: Optional[str] = Field(None, min_length=1, max_length=500)
    item_type: Optional[Literal["normal", "pooled_gift"]] = None
    target_amount: Optional[float] = Field(None, gt=0)


class WishlistItem(WishlistItemBase):
    """Complete wishlist item schema"""
    id: str
    is_purchased: bool = False
    purchased_by: Optional[str] = None
    is_reserved: bool = False
    reserved_by: Optional[str] = None
    current_amount: Optional[float] = 0.0  # For pooled gifts
    contributions: List[Contribution] = []  # List of contributions
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MarkAsPurchasedDTO(BaseModel):
    """Schema for marking an item as purchased"""
    purchased_by: str = Field(..., min_length=1, max_length=100)


class ReserveItemDTO(BaseModel):
    """Schema for reserving an item"""
    reserved_by: str = Field(..., min_length=1, max_length=100)

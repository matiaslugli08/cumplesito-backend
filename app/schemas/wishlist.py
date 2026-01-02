"""
Pydantic schemas for wishlists
"""
from datetime import datetime
from typing import List
from pydantic import BaseModel, Field

from app.schemas.item import WishlistItem


class WishlistBase(BaseModel):
    """Base wishlist schema with common fields"""
    title: str = Field(..., min_length=1, max_length=200)
    owner_name: str = Field(..., min_length=1, max_length=100)
    event_date: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=1)
    allow_anonymous_purchase: bool = True


class WishlistCreate(WishlistBase):
    """Schema for creating a wishlist"""
    pass


class WishlistInDB(WishlistBase):
    """Schema for wishlist from database"""
    id: str
    owner_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WishlistPublic(WishlistInDB):
    """Schema for public wishlist view (includes shareable link)"""
    shareable_link: str

    @classmethod
    def from_db_model(cls, wishlist, base_url: str):
        """Create from database model with generated shareable link"""
        return cls(
            id=wishlist.id,
            title=wishlist.title,
            owner_name=wishlist.owner_name,
            owner_id=wishlist.owner_id,
            event_date=wishlist.event_date,
            description=wishlist.description,
            allow_anonymous_purchase=wishlist.allow_anonymous_purchase,
            created_at=wishlist.created_at,
            updated_at=wishlist.updated_at,
            shareable_link=f"{base_url}/wishlist/{wishlist.id}"
        )


class Wishlist(WishlistPublic):
    """Complete wishlist schema with items"""
    items: List[WishlistItem] = []

    class Config:
        from_attributes = True

    @classmethod
    def from_db_model(cls, wishlist, base_url: str):
        """Create from database model with generated shareable link"""
        return cls(
            id=wishlist.id,
            title=wishlist.title,
            owner_name=wishlist.owner_name,
            owner_id=wishlist.owner_id,
            event_date=wishlist.event_date,
            description=wishlist.description,
            allow_anonymous_purchase=wishlist.allow_anonymous_purchase,
            created_at=wishlist.created_at,
            updated_at=wishlist.updated_at,
            items=[WishlistItem.model_validate(item) for item in wishlist.items],
            shareable_link=f"{base_url}/wishlist/{wishlist.id}"
        )

"""
Pydantic schemas for request/response validation
"""
from app.schemas.user import User, UserCreate, UserLogin, Token
from app.schemas.wishlist import (
    Wishlist,
    WishlistCreate,
    WishlistInDB,
    WishlistPublic,
)
from app.schemas.item import (
    WishlistItem,
    WishlistItemCreate,
    WishlistItemUpdate,
    MarkAsPurchasedDTO,
    ContributionCreate,
    Contribution,
)

__all__ = [
    "User",
    "UserCreate",
    "UserLogin",
    "Token",
    "Wishlist",
    "WishlistCreate",
    "WishlistInDB",
    "WishlistPublic",
    "WishlistItem",
    "WishlistItemCreate",
    "WishlistItemUpdate",
    "MarkAsPurchasedDTO",
    "ContributionCreate",
    "Contribution",
]

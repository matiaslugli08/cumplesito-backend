"""
Pydantic schemas for request/response validation
"""
from app.schemas.user import User, UserCreate, UserLogin, Token, AuthResponse
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
    ReserveItemDTO,
)

__all__ = [
    "User",
    "UserCreate",
    "UserLogin",
    "Token",
    "AuthResponse",
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
    "ReserveItemDTO",
]

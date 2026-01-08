"""
Pydantic schemas for request/response validation
"""
from app.schemas.user import User, UserCreate, UserLogin, Token, AuthResponse, UserMeUpdate
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
from app.schemas.group import (
    GroupCreate,
    GroupUpdate,
    GroupSummary,
    GroupDetail,
    InviteInfo,
    InviteJoinResponse,
    CreateInviteResponse,
    ExpenseCreate,
    ExpenseOut,
    DebtOut,
    DebtUpdate,
)

__all__ = [
    "User",
    "UserCreate",
    "UserLogin",
    "Token",
    "AuthResponse",
    "UserMeUpdate",
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
    "GroupCreate",
    "GroupUpdate",
    "GroupSummary",
    "GroupDetail",
    "InviteInfo",
    "InviteJoinResponse",
    "CreateInviteResponse",
    "ExpenseCreate",
    "ExpenseOut",
    "DebtOut",
    "DebtUpdate",
]

"""
Wishlist routes
Handles CRUD operations for wishlists
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Wishlist as WishlistModel
from app.schemas import Wishlist, WishlistCreate, WishlistPublic
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/wishlists", tags=["Wishlists"])


def get_base_url(request: Request) -> str:
    """Get base URL from request for shareable links"""
    # Get the frontend URL from the Origin header or use a default
    origin = request.headers.get("origin", "http://localhost:3000")
    return origin


@router.post("", response_model=Wishlist, status_code=status.HTTP_201_CREATED)
async def create_wishlist(
    wishlist_data: WishlistCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new wishlist for the authenticated user

    Args:
        wishlist_data: Wishlist creation data
        request: HTTP request for base URL
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created wishlist object
    """
    new_wishlist = WishlistModel(
        title=wishlist_data.title,
        owner_name=wishlist_data.owner_name,
        owner_id=current_user.id,
        event_date=wishlist_data.event_date,
        description=wishlist_data.description,
        allow_anonymous_purchase=wishlist_data.allow_anonymous_purchase
    )

    db.add(new_wishlist)
    db.commit()
    db.refresh(new_wishlist)

    base_url = get_base_url(request)
    return Wishlist.from_db_model(new_wishlist, base_url)


@router.get("", response_model=List[Wishlist])
async def get_user_wishlists(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all wishlists for the authenticated user

    Args:
        request: HTTP request for base URL
        current_user: Current authenticated user
        db: Database session

    Returns:
        List of user's wishlists
    """
    wishlists = db.query(WishlistModel).filter(
        WishlistModel.owner_id == current_user.id
    ).order_by(WishlistModel.created_at.desc()).all()

    base_url = get_base_url(request)
    return [Wishlist.from_db_model(w, base_url) for w in wishlists]


@router.get("/{wishlist_id}", response_model=Wishlist)
async def get_wishlist(
    wishlist_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Get a specific wishlist by ID (public access - no auth required)

    Args:
        wishlist_id: Wishlist ID
        request: HTTP request for base URL
        db: Database session

    Returns:
        Wishlist object

    Raises:
        HTTPException: If wishlist not found
    """
    wishlist = db.query(WishlistModel).filter(
        WishlistModel.id == wishlist_id
    ).first()

    if not wishlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist not found"
        )

    base_url = get_base_url(request)
    return Wishlist.from_db_model(wishlist, base_url)


@router.delete("/{wishlist_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_wishlist(
    wishlist_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a wishlist (only owner can delete)

    Args:
        wishlist_id: Wishlist ID
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException: If wishlist not found or user is not the owner
    """
    wishlist = db.query(WishlistModel).filter(
        WishlistModel.id == wishlist_id
    ).first()

    if not wishlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist not found"
        )

    # Check if user is the owner
    if wishlist.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this wishlist"
        )

    db.delete(wishlist)
    db.commit()

    return None

"""
Wishlist routes
Handles CRUD operations for wishlists
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Wishlist as WishlistModel
from app.schemas import Wishlist, WishlistCreate, WishlistPublic
from app.utils.dependencies import get_current_user
from app.utils.ai_profile_generator import generate_birthday_person_profile

router = APIRouter(prefix="/wishlists", tags=["Wishlists"])


def get_base_url(request: Request) -> str:
    """Get base URL from request for shareable links"""
    # Get the frontend URL from the Origin header or use a default
    origin = request.headers.get("origin", "http://localhost:3000")
    return origin


async def generate_and_update_profile(wishlist_id: str):
    """Generate AI profile for wishlist in background"""
    import logging
    logger = logging.getLogger(__name__)

    # Create a new database session for the background task
    db = next(get_db())

    try:
        wishlist = db.query(WishlistModel).filter(WishlistModel.id == wishlist_id).first()
        if not wishlist:
            logger.warning(f"Wishlist {wishlist_id} not found for profile generation")
            return

        # Prepare items data for AI
        items_data = [
            {
                "title": item.title,
                "description": item.description or ""
            }
            for item in wishlist.items
        ]

        logger.info(f"Generating profile for {wishlist.owner_name} with {len(items_data)} items")

        # Generate profile
        profile = generate_birthday_person_profile(
            items=items_data,
            owner_name=wishlist.owner_name,
            description=wishlist.description
        )

        # Update wishlist with generated profile
        wishlist.birthday_person_profile = profile
        db.commit()

        logger.info(f"Profile generated successfully for wishlist {wishlist_id}")

    except Exception as e:
        logger.error(f"Error generating profile in background: {e}")
        db.rollback()
    finally:
        db.close()


@router.post("", response_model=Wishlist, status_code=status.HTTP_201_CREATED)
async def create_wishlist(
    wishlist_data: WishlistCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new wishlist for the authenticated user
    Automatically generates an AI profile based on the description

    Args:
        wishlist_data: Wishlist creation data
        request: HTTP request for base URL
        background_tasks: FastAPI background tasks
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

    # Generate profile in background (will be available immediately since no items yet)
    background_tasks.add_task(generate_and_update_profile, new_wishlist.id)

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

"""
Wishlist items routes
Handles CRUD operations for items within wishlists
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Wishlist, WishlistItem as WishlistItemModel, Contribution as ContributionModel
from app.schemas import WishlistItem, WishlistItemCreate, WishlistItemUpdate, MarkAsPurchasedDTO, ContributionCreate, Contribution, ReserveItemDTO
from app.utils.dependencies import get_current_user
from app.utils.url_metadata import extract_url_metadata
from app.utils.ai_profile_generator import generate_birthday_person_profile

router = APIRouter(prefix="/wishlists/{wishlist_id}/items", tags=["Wishlist Items"])


def verify_wishlist_owner(wishlist_id: str, user_id: str, db: Session) -> Wishlist:
    """
    Verify that the wishlist exists and the user is the owner

    Args:
        wishlist_id: Wishlist ID
        user_id: User ID to verify ownership
        db: Database session

    Returns:
        Wishlist object

    Raises:
        HTTPException: If wishlist not found or user is not owner
    """
    wishlist = db.query(Wishlist).filter(Wishlist.id == wishlist_id).first()

    if not wishlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist not found"
        )

    if wishlist.owner_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this wishlist"
        )

    return wishlist


async def regenerate_wishlist_profile(wishlist_id: str):
    """Regenerate AI profile for wishlist after items change"""
    import logging
    logger = logging.getLogger(__name__)

    # Create a new database session for the background task
    db = next(get_db())

    try:
        wishlist = db.query(Wishlist).filter(Wishlist.id == wishlist_id).first()
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

        # Generate new profile
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
        logger.error(f"Error regenerating profile: {e}")
        db.rollback()
    finally:
        db.close()


@router.post("", response_model=WishlistItem, status_code=status.HTTP_201_CREATED)
async def add_item(
    wishlist_id: str,
    item_data: WishlistItemCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a new item to a wishlist (owner only)
    Automatically regenerates the birthday person profile

    Args:
        wishlist_id: Wishlist ID
        item_data: Item creation data
        background_tasks: FastAPI background tasks
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created item object
    """
    # Verify ownership
    wishlist = verify_wishlist_owner(wishlist_id, current_user.id, db)

    # If no image URL provided, try to extract from product URL
    image_url = item_data.image_url
    if not image_url and item_data.product_url:
        try:
            metadata = extract_url_metadata(item_data.product_url)
            image_url = metadata.get('image')
        except Exception as e:
            # Log error but continue without image
            print(f"Warning: Could not extract image from URL: {e}")

    # Create new item
    new_item = WishlistItemModel(
        wishlist_id=wishlist_id,
        title=item_data.title,
        description=item_data.description,
        image_url=image_url,
        product_url=item_data.product_url,
        item_type=item_data.item_type,
        target_amount=item_data.target_amount,
        current_amount=0.0 if item_data.item_type == 'pooled_gift' else None
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    # Regenerate profile in background with the new item
    background_tasks.add_task(regenerate_wishlist_profile, wishlist_id)

    return new_item


@router.put("/{item_id}", response_model=WishlistItem)
async def update_item(
    wishlist_id: str,
    item_id: str,
    item_data: WishlistItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a wishlist item (owner only)

    Args:
        wishlist_id: Wishlist ID
        item_id: Item ID
        item_data: Item update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Updated item object

    Raises:
        HTTPException: If item not found
    """
    # Verify ownership
    verify_wishlist_owner(wishlist_id, current_user.id, db)

    # Find item
    item = db.query(WishlistItemModel).filter(
        WishlistItemModel.id == item_id,
        WishlistItemModel.wishlist_id == wishlist_id
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    # Update fields that are provided
    update_data = item_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item, field, value)

    db.commit()
    db.refresh(item)

    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    wishlist_id: str,
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a wishlist item (owner only)

    Args:
        wishlist_id: Wishlist ID
        item_id: Item ID
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException: If item not found
    """
    # Verify ownership
    verify_wishlist_owner(wishlist_id, current_user.id, db)

    # Find and delete item
    item = db.query(WishlistItemModel).filter(
        WishlistItemModel.id == item_id,
        WishlistItemModel.wishlist_id == wishlist_id
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    db.delete(item)
    db.commit()

    return None


@router.post("/{item_id}/purchase", response_model=WishlistItem)
async def mark_as_purchased(
    wishlist_id: str,
    item_id: str,
    purchase_data: MarkAsPurchasedDTO,
    db: Session = Depends(get_db)
):
    """
    Mark an item as purchased (public access - no auth required)

    Args:
        wishlist_id: Wishlist ID
        item_id: Item ID
        purchase_data: Purchase data (who purchased it)
        db: Database session

    Returns:
        Updated item object

    Raises:
        HTTPException: If wishlist or item not found, or item already purchased
    """
    # Verify wishlist exists
    wishlist = db.query(Wishlist).filter(Wishlist.id == wishlist_id).first()
    if not wishlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist not found"
        )

    # Find item
    item = db.query(WishlistItemModel).filter(
        WishlistItemModel.id == item_id,
        WishlistItemModel.wishlist_id == wishlist_id
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    if item.is_purchased:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item already purchased"
        )

    # Mark as purchased
    item.is_purchased = True
    item.purchased_by = purchase_data.purchased_by

    db.commit()
    db.refresh(item)

    return item


@router.delete("/{item_id}/purchase", response_model=WishlistItem)
async def unmark_as_purchased(
    wishlist_id: str,
    item_id: str,
    db: Session = Depends(get_db)
):
    """
    Unmark an item as purchased (public access - no auth required)

    Args:
        wishlist_id: Wishlist ID
        item_id: Item ID
        db: Database session

    Returns:
        Updated item object

    Raises:
        HTTPException: If wishlist or item not found
    """
    # Verify wishlist exists
    wishlist = db.query(Wishlist).filter(Wishlist.id == wishlist_id).first()
    if not wishlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist not found"
        )

    # Find item
    item = db.query(WishlistItemModel).filter(
        WishlistItemModel.id == item_id,
        WishlistItemModel.wishlist_id == wishlist_id
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    # Unmark as purchased
    item.is_purchased = False
    item.purchased_by = None

    db.commit()
    db.refresh(item)

    return item


@router.post("/{item_id}/contribute", response_model=WishlistItem)
async def contribute_to_pooled_gift(
    wishlist_id: str,
    item_id: str,
    contribution_data: ContributionCreate,
    db: Session = Depends(get_db)
):
    """
    Contribute to a pooled gift item (public access - no auth required)

    Args:
        wishlist_id: Wishlist ID
        item_id: Item ID
        contribution_data: Contribution data (name, amount, message)
        db: Database session

    Returns:
        Updated item object with contribution

    Raises:
        HTTPException: If wishlist/item not found or item is not a pooled gift
    """
    # Verify wishlist exists
    wishlist = db.query(Wishlist).filter(Wishlist.id == wishlist_id).first()
    if not wishlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist not found"
        )

    # Find item
    item = db.query(WishlistItemModel).filter(
        WishlistItemModel.id == item_id,
        WishlistItemModel.wishlist_id == wishlist_id
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    # Verify it's a pooled gift
    if item.item_type != "pooled_gift":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This item is not a pooled gift"
        )

    # Create contribution
    contribution = ContributionModel(
        item_id=item_id,
        contributor_name=contribution_data.contributor_name,
        amount=contribution_data.amount,
        message=contribution_data.message
    )

    # Update item's current amount
    item.current_amount = (item.current_amount or 0.0) + contribution_data.amount

    # Mark as purchased if target reached
    if item.target_amount and item.current_amount >= item.target_amount:
        item.is_purchased = True

    db.add(contribution)
    db.commit()
    db.refresh(item)

    return item


@router.get("/{item_id}/contributions", response_model=list[Contribution])
async def get_item_contributions(
    wishlist_id: str,
    item_id: str,
    db: Session = Depends(get_db)
):
    """
    Get all contributions for a pooled gift item (public access)

    Args:
        wishlist_id: Wishlist ID
        item_id: Item ID
        db: Database session

    Returns:
        List of contributions

    Raises:
        HTTPException: If wishlist or item not found
    """
    # Verify wishlist and item exist
    item = db.query(WishlistItemModel).filter(
        WishlistItemModel.id == item_id,
        WishlistItemModel.wishlist_id == wishlist_id
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    return item.contributions


@router.post("/{item_id}/reserve", response_model=WishlistItem)
async def reserve_item(
    wishlist_id: str,
    item_id: str,
    reserve_data: ReserveItemDTO,
    db: Session = Depends(get_db)
):
    """
    Reserve an item (public access - no auth required)
    Only works for normal items, not pooled gifts

    Args:
        wishlist_id: Wishlist ID
        item_id: Item ID
        reserve_data: Reservation data (reserved_by name)
        db: Database session

    Returns:
        Updated item object

    Raises:
        HTTPException: If wishlist/item not found or item is already reserved/purchased
    """
    # Verify wishlist exists
    wishlist = db.query(Wishlist).filter(Wishlist.id == wishlist_id).first()
    if not wishlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist not found"
        )

    # Find item
    item = db.query(WishlistItemModel).filter(
        WishlistItemModel.id == item_id,
        WishlistItemModel.wishlist_id == wishlist_id
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    # Cannot reserve pooled gifts
    if item.item_type == "pooled_gift":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot reserve pooled gifts. Use contribute instead."
        )

    # Check if already purchased
    if item.is_purchased:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Item is already purchased"
        )

    # Check if already reserved
    if item.is_reserved:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Item is already reserved by {item.reserved_by}"
        )

    # Reserve the item
    item.is_reserved = True
    item.reserved_by = reserve_data.reserved_by

    db.commit()
    db.refresh(item)

    return item


@router.delete("/{item_id}/reserve", response_model=WishlistItem)
async def unreserve_item(
    wishlist_id: str,
    item_id: str,
    db: Session = Depends(get_db)
):
    """
    Unreserve an item (public access - no auth required)

    Args:
        wishlist_id: Wishlist ID
        item_id: Item ID
        db: Database session

    Returns:
        Updated item object

    Raises:
        HTTPException: If wishlist or item not found
    """
    # Verify wishlist exists
    wishlist = db.query(Wishlist).filter(Wishlist.id == wishlist_id).first()
    if not wishlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wishlist not found"
        )

    # Find item
    item = db.query(WishlistItemModel).filter(
        WishlistItemModel.id == item_id,
        WishlistItemModel.wishlist_id == wishlist_id
    ).first()

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Item not found"
        )

    # Unreserve the item
    item.is_reserved = False
    item.reserved_by = None

    db.commit()
    db.refresh(item)

    return item

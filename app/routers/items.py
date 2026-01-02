"""
Wishlist items routes
Handles CRUD operations for items within wishlists
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Wishlist, WishlistItem as WishlistItemModel
from app.schemas import WishlistItem, WishlistItemCreate, WishlistItemUpdate, MarkAsPurchasedDTO
from app.utils.dependencies import get_current_user
from app.utils.url_metadata import extract_url_metadata

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


@router.post("", response_model=WishlistItem, status_code=status.HTTP_201_CREATED)
async def add_item(
    wishlist_id: str,
    item_data: WishlistItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a new item to a wishlist (owner only)

    Args:
        wishlist_id: Wishlist ID
        item_data: Item creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        Created item object
    """
    # Verify ownership
    verify_wishlist_owner(wishlist_id, current_user.id, db)

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
        product_url=item_data.product_url
    )

    db.add(new_item)
    db.commit()
    db.refresh(new_item)

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

"""
Debug routes for testing profile generation
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.models import Wishlist
from app.utils.ai_profile_generator import generate_birthday_person_profile

router = APIRouter(prefix="/debug", tags=["Debug"])
logger = logging.getLogger(__name__)


@router.post("/regenerate-profile/{wishlist_id}")
async def force_regenerate_profile(
    wishlist_id: str,
    db: Session = Depends(get_db)
):
    """
    Force regenerate profile for a wishlist (for debugging)
    """
    logger.info(f"🔧 DEBUG: Force regenerating profile for wishlist {wishlist_id}")

    wishlist = db.query(Wishlist).filter(Wishlist.id == wishlist_id).first()

    if not wishlist:
        raise HTTPException(status_code=404, detail="Wishlist not found")

    # Prepare items data - EXCLUDE pooled_gift items
    items_data = [
        {
            "title": item.title,
            "description": item.description or ""
        }
        for item in wishlist.items
        if item.item_type != "pooled_gift"  # Excluir items de tipo colecta
    ]

    logger.info(f"🔧 DEBUG: Wishlist owner: {wishlist.owner_name}")
    logger.info(f"🔧 DEBUG: Wishlist title: {wishlist.title}")
    logger.info(f"🔧 DEBUG: Description: {wishlist.description}")
    logger.info(f"🔧 DEBUG: Items count: {len(items_data)} (excluding pooled gifts)")
    logger.info(f"🔧 DEBUG: Items: {items_data}")

    # Generate profile (only if there are items)
    profile = generate_birthday_person_profile(
        items=items_data,
        owner_name=wishlist.owner_name,
        description=wishlist.description,
        wishlist_title=wishlist.title
    )

    # Update wishlist (or None if no profile was generated)
    wishlist.birthday_person_profile = profile if profile else None
    db.commit()
    db.refresh(wishlist)

    return {
        "success": True,
        "wishlist_id": wishlist_id,
        "profile": profile if profile else "No profile generated (no items)",
        "items_analyzed": len(items_data),
        "profile_generated": bool(profile)
    }

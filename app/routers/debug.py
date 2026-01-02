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

    # Prepare items data
    items_data = [
        {
            "title": item.title,
            "description": item.description or ""
        }
        for item in wishlist.items
    ]

    logger.info(f"🔧 DEBUG: Wishlist owner: {wishlist.owner_name}")
    logger.info(f"🔧 DEBUG: Description: {wishlist.description}")
    logger.info(f"🔧 DEBUG: Items count: {len(items_data)}")
    logger.info(f"🔧 DEBUG: Items: {items_data}")

    # Generate profile
    profile = generate_birthday_person_profile(
        items=items_data,
        owner_name=wishlist.owner_name,
        description=wishlist.description
    )

    # Update wishlist
    wishlist.birthday_person_profile = profile
    db.commit()
    db.refresh(wishlist)

    return {
        "success": True,
        "wishlist_id": wishlist_id,
        "profile": profile,
        "items_analyzed": len(items_data)
    }

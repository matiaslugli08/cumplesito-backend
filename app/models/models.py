"""
SQLAlchemy database models
Defines the database schema for users, wishlists, and items
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.database import Base


def generate_uuid():
    """Generate a UUID string"""
    return str(uuid.uuid4())


class User(Base):
    """User model for authentication and wishlist ownership"""
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    wishlists = relationship("Wishlist", back_populates="owner", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"


class Wishlist(Base):
    """Wishlist model for birthday/event wishlists"""
    __tablename__ = "wishlists"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String(200), nullable=False)
    owner_name = Column(String(100), nullable=False)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    event_date = Column(String(50), nullable=False)  # Store as string for flexibility
    description = Column(Text, nullable=False)
    allow_anonymous_purchase = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    owner = relationship("User", back_populates="wishlists")
    items = relationship("WishlistItem", back_populates="wishlist", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Wishlist {self.title}>"


class WishlistItem(Base):
    """Individual gift item in a wishlist"""
    __tablename__ = "wishlist_items"

    id = Column(String, primary_key=True, default=generate_uuid)
    wishlist_id = Column(String, ForeignKey("wishlists.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    image_url = Column(String(500), nullable=True)  # Optional - can be auto-detected
    product_url = Column(String(500), nullable=False)
    is_purchased = Column(Boolean, default=False, nullable=False)
    purchased_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    wishlist = relationship("Wishlist", back_populates="items")

    def __repr__(self):
        return f"<WishlistItem {self.title}>"

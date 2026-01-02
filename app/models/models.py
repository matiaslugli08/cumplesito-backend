"""
SQLAlchemy database models
Defines the database schema for users, wishlists, and items
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Float, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum

from app.database import Base


class ItemType(str, enum.Enum):
    """Enum for item types"""
    NORMAL = "normal"
    POOLED_GIFT = "pooled_gift"  # Colecta/regalo grupal


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
    birthday_person_profile = Column(Text, nullable=True)  # AI-generated profile based on items
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
    product_url = Column(String(500), nullable=True)  # Optional
    is_purchased = Column(Boolean, default=False, nullable=False)
    purchased_by = Column(String(100), nullable=True)
    
    # Pooled gift (colecta) fields
    item_type = Column(String(20), default="normal", nullable=False)  # "normal" or "pooled_gift"
    target_amount = Column(Float, nullable=True)  # Monto objetivo para colectas
    current_amount = Column(Float, default=0.0, nullable=True)  # Monto actual recolectado
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    wishlist = relationship("Wishlist", back_populates="items")
    contributions = relationship("Contribution", back_populates="item", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<WishlistItem {self.title}>"


class Contribution(Base):
    """Contribution to a pooled gift item"""
    __tablename__ = "contributions"

    id = Column(String, primary_key=True, default=generate_uuid)
    item_id = Column(String, ForeignKey("wishlist_items.id"), nullable=False)
    contributor_name = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    message = Column(Text, nullable=True)  # Optional message from contributor
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    item = relationship("WishlistItem", back_populates="contributions")

    def __repr__(self):
        return f"<Contribution {self.contributor_name}: ${self.amount}>"

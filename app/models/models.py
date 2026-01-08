"""
SQLAlchemy database models
Defines the database schema for users, wishlists, and items
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Date, ForeignKey, Text, Float, Integer
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
    # Birth date (used for reminders). Nullable for backward compatibility with existing DBs.
    birthday = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    wishlists = relationship("Wishlist", back_populates="owner", cascade="all, delete-orphan")
    group_memberships = relationship("GroupMember", back_populates="user", cascade="all, delete-orphan")

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

    # Reserved state (for normal items)
    is_reserved = Column(Boolean, default=False, nullable=False)
    reserved_by = Column(String(100), nullable=True)

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


class GroupRole(str, enum.Enum):
    OWNER = "OWNER"
    MEMBER = "MEMBER"


class DebtStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"


class Group(Base):
    __tablename__ = "groups"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(200), nullable=False)
    created_by_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")
    invites = relationship("GroupInvite", back_populates="group", cascade="all, delete-orphan")
    expenses = relationship("GroupGiftExpense", back_populates="group", cascade="all, delete-orphan")


class GroupInvite(Base):
    __tablename__ = "group_invites"

    id = Column(String, primary_key=True, default=generate_uuid)
    group_id = Column(String, ForeignKey("groups.id"), nullable=False, index=True)
    token = Column(String(128), unique=True, nullable=False, index=True)
    created_by_user_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    max_uses = Column(Integer, nullable=True)
    uses_count = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    group = relationship("Group", back_populates="invites")


class GroupMember(Base):
    __tablename__ = "group_members"

    id = Column(String, primary_key=True, default=generate_uuid)
    group_id = Column(String, ForeignKey("groups.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String(20), default=GroupRole.MEMBER.value, nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    group = relationship("Group", back_populates="members")
    user = relationship("User", back_populates="group_memberships")


class GroupGiftExpense(Base):
    __tablename__ = "group_gift_expenses"

    id = Column(String, primary_key=True, default=generate_uuid)
    group_id = Column(String, ForeignKey("groups.id"), nullable=False, index=True)
    birthday_user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    paid_by_user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=True)  # e.g. "Cumple de Mati"
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="UYU", nullable=False)
    payment_account = Column(String(255), nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    group = relationship("Group", back_populates="expenses")
    debts = relationship("GroupGiftDebt", back_populates="expense", cascade="all, delete-orphan")


class GroupGiftDebt(Base):
    __tablename__ = "group_gift_debts"

    id = Column(String, primary_key=True, default=generate_uuid)
    expense_id = Column(String, ForeignKey("group_gift_expenses.id"), nullable=False, index=True)
    owed_by_user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    owed_to_user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    status = Column(String(20), default=DebtStatus.PENDING.value, nullable=False)
    paid_at = Column(DateTime, nullable=True)

    expense = relationship("GroupGiftExpense", back_populates="debts")


class EmailNotificationType(str, enum.Enum):
    BIRTHDAY_30_DAYS = "BIRTHDAY_30_DAYS"
    GROUP_BIRTHDAY_14_DAYS = "GROUP_BIRTHDAY_14_DAYS"


class EmailNotificationLog(Base):
    __tablename__ = "email_notification_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    notification_type = Column(String(50), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)  # recipient
    group_id = Column(String, ForeignKey("groups.id"), nullable=True, index=True)
    target_user_id = Column(String, ForeignKey("users.id"), nullable=True, index=True)  # birthday person
    target_date = Column(Date, nullable=False, index=True)  # occurrence date (year included)
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)

"""
Pydantic schemas for Regalos Colectivos (Groups + Invites + Expenses/Debts)
"""

from datetime import datetime, date
from typing import List, Optional, Literal

from pydantic import BaseModel, Field


class GroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)


class GroupUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)


class GroupSummary(BaseModel):
    id: str
    name: str
    member_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class GroupMemberUser(BaseModel):
    id: str
    name: str
    email: str
    birthday: Optional[date] = None

    class Config:
        from_attributes = True


class GroupMemberOut(BaseModel):
    id: str
    role: str
    joined_at: datetime
    user: GroupMemberUser

    class Config:
        from_attributes = True


class GroupDetail(BaseModel):
    id: str
    name: str
    created_by_user_id: str
    created_at: datetime
    members: List[GroupMemberOut] = []

    class Config:
        from_attributes = True


class InviteInfo(BaseModel):
    group_id: str
    group_name: str
    is_valid: bool


class InviteJoinResponse(BaseModel):
    group_id: str
    group_name: str
    joined: bool


class CreateInviteResponse(BaseModel):
    group_id: str
    token: str
    invite_url: str
    expires_at: Optional[datetime] = None


class ExpenseCreate(BaseModel):
    birthday_user_id: str
    title: str = Field(..., min_length=1, max_length=200)
    participant_user_ids: Optional[List[str]] = None  # If omitted, defaults to all group members except payer
    amount: float = Field(..., gt=0)
    currency: str = Field("UYU", min_length=1, max_length=10)
    payment_account: str = Field(..., min_length=1, max_length=255)
    note: Optional[str] = Field(None, max_length=1000)


class ExpenseOut(BaseModel):
    id: str
    group_id: str
    birthday_user_id: str
    paid_by_user_id: str
    title: Optional[str] = None
    amount: float
    currency: str
    payment_account: str
    note: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DebtOut(BaseModel):
    id: str
    expense_id: str
    owed_by_user_id: str
    owed_to_user_id: str
    amount: float
    status: Literal["PENDING", "PAID"]
    paid_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DebtUpdate(BaseModel):
    status: Literal["PENDING", "PAID"]

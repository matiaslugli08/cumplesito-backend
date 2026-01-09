"""
Regalos Colectivos routes:
- Groups (create/list/detail)
- Invites (create/validate/join)
- Expenses/Debts (create/list/update)
"""

from datetime import datetime, timedelta, date as date_type
import secrets
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import (
    User,
    Group,
    GroupInvite,
    GroupMember,
    GroupGiftExpense,
    GroupGiftDebt,
)
from app.schemas import (
    GroupCreate,
    GroupUpdate,
    GroupSummary,
    GroupDetail,
    InviteInfo,
    InviteJoinResponse,
    CreateInviteResponse,
    ExpenseCreate,
    ExpenseOut,
    DebtOut,
    DebtUpdate,
)
from app.utils.dependencies import get_current_user


router = APIRouter(tags=["Collective Gifts"])


def _get_origin(request: Request) -> str:
    return request.headers.get("origin", "http://localhost:5173")


def _new_invite_token() -> str:
    # 32+ chars, non-guessable
    return secrets.token_urlsafe(32)


def _get_group_for_member(db: Session, group_id: str, user_id: str) -> Group:
    group = (
        db.query(Group)
        .join(GroupMember, GroupMember.group_id == Group.id)
        .filter(Group.id == group_id, GroupMember.user_id == user_id)
        .first()
    )
    if not group:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this group")
    return group


def _require_group_owner(db: Session, group_id: str, user_id: str) -> Group:
    member = (
        db.query(GroupMember)
        .filter(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this group")
    if member.role != "OWNER":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    return group


def _validate_invite(invite: GroupInvite) -> None:
    if not invite.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite is inactive")
    now = datetime.utcnow()
    if invite.expires_at and now > invite.expires_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite has expired")
    if invite.max_uses is not None and invite.uses_count >= invite.max_uses:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite max uses reached")


@router.post("/groups", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_group(
    body: GroupCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = Group(name=body.name, created_by_user_id=current_user.id)
    db.add(group)
    db.commit()
    db.refresh(group)

    # owner membership
    member = GroupMember(group_id=group.id, user_id=current_user.id, role="OWNER")
    db.add(member)

    # invite token (default: 60 days)
    token = _new_invite_token()
    invite = GroupInvite(
        group_id=group.id,
        token=token,
        created_by_user_id=current_user.id,
        expires_at=datetime.utcnow() + timedelta(days=60),
        is_active=True,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)

    invite_url = f"{_get_origin(request)}/invite/{invite.token}"

    return {
        "group": GroupDetail.model_validate(
            db.query(Group).filter(Group.id == group.id).first()
        ),
        "invite_url": invite_url,
    }


@router.get("/groups/my", response_model=list[GroupSummary])
async def get_my_groups(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # member_count via subquery
    member_counts = (
        db.query(GroupMember.group_id.label("group_id"), func.count(GroupMember.id).label("member_count"))
        .group_by(GroupMember.group_id)
        .subquery()
    )

    rows = (
        db.query(Group, member_counts.c.member_count)
        .join(GroupMember, GroupMember.group_id == Group.id)
        .join(member_counts, member_counts.c.group_id == Group.id)
        .filter(GroupMember.user_id == current_user.id)
        .order_by(Group.created_at.desc())
        .all()
    )

    result: list[GroupSummary] = []
    for group, member_count in rows:
        result.append(
            GroupSummary(
                id=group.id,
                name=group.name,
                member_count=int(member_count or 0),
                created_at=group.created_at,
            )
        )
    return result


@router.get("/groups/{group_id}", response_model=GroupDetail)
async def get_group_detail(
    group_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_group_for_member(db, group_id, current_user.id)
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    # Ensure members include user relationship
    _ = group.members
    return GroupDetail.model_validate(group)


@router.patch("/groups/{group_id}", response_model=GroupDetail)
async def update_group(
    group_id: str,
    body: GroupUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Any group member can rename (as requested)
    _get_group_for_member(db, group_id, current_user.id)
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    group.name = body.name
    db.commit()
    db.refresh(group)
    _ = group.members
    return GroupDetail.model_validate(group)


@router.post("/groups/{group_id}/invites", response_model=CreateInviteResponse, status_code=status.HTTP_201_CREATED)
async def create_group_invite(
    group_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Any group member can generate an invite link
    _get_group_for_member(db, group_id, current_user.id)

    token = _new_invite_token()
    invite = GroupInvite(
        group_id=group_id,
        token=token,
        created_by_user_id=current_user.id,
        expires_at=datetime.utcnow() + timedelta(days=60),
        is_active=True,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)

    invite_url = f"{_get_origin(request)}/invite/{invite.token}"
    return CreateInviteResponse(group_id=group_id, token=invite.token, invite_url=invite_url, expires_at=invite.expires_at)


@router.get("/invites/{token}", response_model=InviteInfo)
async def get_invite_info(token: str, db: Session = Depends(get_db)):
    invite = db.query(GroupInvite).filter(GroupInvite.token == token).first()
    if not invite:
        return InviteInfo(group_id="", group_name="", is_valid=False)
    try:
        _validate_invite(invite)
    except HTTPException:
        group = db.query(Group).filter(Group.id == invite.group_id).first()
        return InviteInfo(group_id=invite.group_id, group_name=group.name if group else "", is_valid=False)

    group = db.query(Group).filter(Group.id == invite.group_id).first()
    return InviteInfo(group_id=invite.group_id, group_name=group.name if group else "", is_valid=True)


@router.post("/invites/{token}/join", response_model=InviteJoinResponse)
async def join_invite(
    token: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    invite = db.query(GroupInvite).filter(GroupInvite.token == token).first()
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    _validate_invite(invite)

    group = db.query(Group).filter(Group.id == invite.group_id).first()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    existing = (
        db.query(GroupMember)
        .filter(GroupMember.group_id == group.id, GroupMember.user_id == current_user.id)
        .first()
    )
    if existing:
        return InviteJoinResponse(group_id=group.id, group_name=group.name, joined=False)

    member = GroupMember(group_id=group.id, user_id=current_user.id, role="MEMBER")
    db.add(member)
    invite.uses_count = (invite.uses_count or 0) + 1
    db.commit()

    return InviteJoinResponse(group_id=group.id, group_name=group.name, joined=True)


@router.post("/groups/{group_id}/expenses", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
async def create_expense(
    group_id: str,
    body: ExpenseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_group_for_member(db, group_id, current_user.id)

    # Prevent selecting yourself as honoree for an expense you are creating
    if body.birthday_user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="birthday_user_id cannot be the payer")

    # birthday user must be member
    birthday_member = (
        db.query(GroupMember)
        .filter(GroupMember.group_id == group_id, GroupMember.user_id == body.birthday_user_id)
        .first()
    )
    if not birthday_member:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="birthday_user_id must be a group member")

    expense = GroupGiftExpense(
        group_id=group_id,
        birthday_user_id=body.birthday_user_id,
        paid_by_user_id=current_user.id,
        title=body.title,
        amount=body.amount,
        currency=body.currency,
        payment_account=body.payment_account,
        note=body.note,
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)

    # Create debts for selected participants (split evenly).
    # If participant_user_ids not provided, default to all group members except payer.
    members = db.query(GroupMember).filter(GroupMember.group_id == group_id).all()
    member_user_ids = {m.user_id for m in members}

    if body.participant_user_ids is None:
        debtor_user_ids = [m.user_id for m in members if m.user_id != current_user.id]
    else:
        requested = [uid for uid in body.participant_user_ids if uid != current_user.id]
        invalid = [uid for uid in requested if uid not in member_user_ids]
        if invalid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="participant_user_ids must be group members")
        # de-dup while keeping order
        seen: set[str] = set()
        debtor_user_ids = []
        for uid in requested:
            if uid not in seen:
                seen.add(uid)
                debtor_user_ids.append(uid)

    if not debtor_user_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No participants selected")

    split = float(body.amount) / float(len(debtor_user_ids))
    for owed_by in debtor_user_ids:
        debt = GroupGiftDebt(
            expense_id=expense.id,
            owed_by_user_id=owed_by,
            owed_to_user_id=current_user.id,
            amount=split,
            status="PENDING",
            paid_at=None,
        )
        db.add(debt)
    db.commit()

    return ExpenseOut.model_validate(expense)


@router.delete("/groups/{group_id}/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    group_id: str,
    expense_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_group_for_member(db, group_id, current_user.id)
    expense = db.query(GroupGiftExpense).filter(GroupGiftExpense.id == expense_id).first()
    if not expense or expense.group_id != group_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    db.delete(expense)
    db.commit()
    return None


@router.get("/groups/{group_id}/expenses", response_model=list[ExpenseOut])
async def list_expenses(
    group_id: str,
    birthday_user_id: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_group_for_member(db, group_id, current_user.id)
    q = db.query(GroupGiftExpense).filter(GroupGiftExpense.group_id == group_id)
    if birthday_user_id:
        q = q.filter(GroupGiftExpense.birthday_user_id == birthday_user_id)
    return [ExpenseOut.model_validate(e) for e in q.order_by(GroupGiftExpense.created_at.desc()).all()]


@router.get("/expenses/{expense_id}/debts", response_model=list[DebtOut])
async def list_debts(
    expense_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    expense = db.query(GroupGiftExpense).filter(GroupGiftExpense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    _get_group_for_member(db, expense.group_id, current_user.id)
    debts = db.query(GroupGiftDebt).filter(GroupGiftDebt.expense_id == expense_id).all()
    return [DebtOut.model_validate(d) for d in debts]


@router.patch("/debts/{debt_id}", response_model=DebtOut)
async def update_debt(
    debt_id: str,
    body: DebtUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    debt = db.query(GroupGiftDebt).filter(GroupGiftDebt.id == debt_id).first()
    if not debt:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Debt not found")

    expense = db.query(GroupGiftExpense).filter(GroupGiftExpense.id == debt.expense_id).first()
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")

    _get_group_for_member(db, expense.group_id, current_user.id)

    # Permissions:
    # - payer (owed_to) can mark PAID/PENDING
    # - debtor (owed_by) can mark their own as PAID (self-report "I paid my part")
    is_payer = debt.owed_to_user_id == current_user.id
    is_debtor = debt.owed_by_user_id == current_user.id
    if not (is_payer or is_debtor):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this debt")
    if is_debtor and body.status != "PAID":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only payer can mark as pending")

    debt.status = body.status
    debt.paid_at = datetime.utcnow() if body.status == "PAID" else None
    db.commit()
    db.refresh(debt)
    return DebtOut.model_validate(debt)


@router.delete("/groups/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    group_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Any member can remove members (as requested)
    _get_group_for_member(db, group_id, current_user.id)

    member = db.query(GroupMember).filter(GroupMember.group_id == group_id, GroupMember.user_id == user_id).first()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    # Keep at least one OWNER: if removing the last owner, promote another member if possible.
    if member.role == "OWNER":
        owners = db.query(GroupMember).filter(GroupMember.group_id == group_id, GroupMember.role == "OWNER").all()
        if len(owners) == 1:
            replacement = (
                db.query(GroupMember)
                .filter(GroupMember.group_id == group_id, GroupMember.user_id != user_id)
                .order_by(GroupMember.joined_at.asc())
                .first()
            )
            if replacement:
                replacement.role = "OWNER"
            # If no replacement, deleting would leave group without owner; block.
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove the last member")

    db.delete(member)
    db.commit()
    return None

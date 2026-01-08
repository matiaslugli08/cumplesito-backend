"""
Daily email reminders scheduler job.

Rules:
1) Global reminder: ~30 days before user's next birthday -> email to that user.
2) Group reminder: 14 days before a member's next birthday -> email to group members.

Anti-duplicate via EmailNotificationLog unique constraint.
"""

from __future__ import annotations

from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import (
    User,
    Group,
    GroupMember,
    EmailNotificationLog,
)
from app.utils.emailer import is_email_configured, send_email


def _safe_next_birthday(birthday: date, today: date) -> date:
    """
    Compute next occurrence of birthday relative to today, ignoring birth year.
    Handles Feb 29 in non-leap years by using Feb 28.
    """
    month, day = birthday.month, birthday.day
    year = today.year
    try:
        candidate = date(year, month, day)
    except ValueError:
        # Feb 29 -> Feb 28 on non-leap years
        candidate = date(year, 2, 28)
    if candidate < today:
        year += 1
        try:
            candidate = date(year, month, day)
        except ValueError:
            candidate = date(year, 2, 28)
    return candidate


def _already_sent(
    db: Session,
    notification_type: str,
    user_id: str,
    target_date: date,
    group_id: str | None = None,
    target_user_id: str | None = None,
) -> bool:
    q = db.query(EmailNotificationLog).filter(
        EmailNotificationLog.notification_type == notification_type,
        EmailNotificationLog.user_id == user_id,
        EmailNotificationLog.target_date == target_date,
        EmailNotificationLog.group_id.is_(group_id) if group_id is None else EmailNotificationLog.group_id == group_id,
        EmailNotificationLog.target_user_id.is_(target_user_id)
        if target_user_id is None
        else EmailNotificationLog.target_user_id == target_user_id,
    )
    return db.query(q.exists()).scalar() is True


def _log_sent(
    db: Session,
    notification_type: str,
    user_id: str,
    target_date: date,
    group_id: str | None = None,
    target_user_id: str | None = None,
) -> None:
    db.add(
        EmailNotificationLog(
            notification_type=notification_type,
            user_id=user_id,
            group_id=group_id,
            target_user_id=target_user_id,
            target_date=target_date,
            sent_at=datetime.utcnow(),
        )
    )


def run_daily_reminders() -> None:
    """
    Scheduler entrypoint.
    Safe no-op if SMTP isn't configured or reminders disabled.
    """
    if not settings.EMAIL_REMINDERS_ENABLED:
        return
    if not is_email_configured():
        # Avoid crashing the app if not configured; just do nothing.
        return

    tz = ZoneInfo(settings.EMAIL_TIMEZONE)
    today = datetime.now(tz=tz).date()

    db = SessionLocal()
    try:
        _send_birthday_30_days(db, today)
        _send_group_14_days(db, today)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _send_birthday_30_days(db: Session, today: date) -> None:
    users = db.query(User).filter(User.birthday.is_not(None)).all()
    for user in users:
        next_bday = _safe_next_birthday(user.birthday, today)
        days_until = (next_bday - today).days
        # Allow 30-31 to handle month-length edge cases
        if days_until not in (30, 31):
            continue

        ntype = "BIRTHDAY_30_DAYS"
        if _already_sent(db, ntype, user.id, next_bday):
            continue

        subject = "🎂 Tu cumple se acerca: armá tu lista en Cumplesito"
        body = (
            f"Hola {user.name}!\n\n"
            f"Tu cumple se acerca ({next_bday.strftime('%Y-%m-%d')}).\n"
            "Entrá a Cumplesito y armá tu lista así tus amigos la ven a tiempo.\n\n"
            f"{settings.FRONTEND_BASE_URL}\n"
        )
        send_email(user.email, subject, body)
        _log_sent(db, ntype, user.id, next_bday)


def _send_group_14_days(db: Session, today: date) -> None:
    # Preload memberships to avoid N+1 explosion in small scale; acceptable for now.
    groups = db.query(Group).all()
    for group in groups:
        members = db.query(GroupMember).filter(GroupMember.group_id == group.id).all()
        member_user_ids = [m.user_id for m in members]
        if not member_user_ids:
            continue

        users = db.query(User).filter(User.id.in_(member_user_ids), User.birthday.is_not(None)).all()
        users_by_id = {u.id: u for u in users}

        # For each birthday person in group...
        for birthday_user in users:
            next_bday = _safe_next_birthday(birthday_user.birthday, today)
            if (next_bday - today).days != 14:
                continue

            # email all members (excluding birthday person by default)
            for recipient_id in member_user_ids:
                if recipient_id == birthday_user.id:
                    continue
                recipient = users_by_id.get(recipient_id)
                if not recipient:
                    # recipient has no birthday or not loaded; still can receive email (needs email/name)
                    recipient = db.query(User).filter(User.id == recipient_id).first()
                if not recipient:
                    continue

                ntype = "GROUP_BIRTHDAY_14_DAYS"
                if _already_sent(db, ntype, recipient.id, next_bday, group_id=group.id, target_user_id=birthday_user.id):
                    continue

                subject = f"🎁 Recordatorio: cumple de {birthday_user.name} en 2 semanas"
                body = (
                    f"Hola {recipient.name}!\n\n"
                    f"En 2 semanas es el cumple de {birthday_user.name} ({next_bday.strftime('%Y-%m-%d')}).\n"
                    f"Grupo: {group.name}\n\n"
                    "Entren al grupo para organizar el regalo.\n\n"
                    f"{settings.FRONTEND_BASE_URL}\n"
                )
                send_email(recipient.email, subject, body)
                _log_sent(db, ntype, recipient.id, next_bday, group_id=group.id, target_user_id=birthday_user.id)

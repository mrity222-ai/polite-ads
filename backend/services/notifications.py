import sys
from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from entities import Notification

def create_notification(
    db: Session,
    user_id: str,
    title: str,
    message: str,
    notif_type: str = "info",
    action_url: Optional[str] = None
) -> Notification:
    """
    Creates an in-app notification record for a user.
    """
    notif = Notification(
        user_id=user_id,
        type=notif_type,
        title=title,
        message=message,
        action_url=action_url,
        is_read=False
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif

def get_user_notifications(
    db: Session,
    user_id: str,
    limit: int = 30
) -> List[Notification]:
    """
    Retrieves recent in-app notifications for the user.
    """
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .all()
    )

def get_unread_count(db: Session, user_id: str) -> int:
    """
    Returns the count of unread notifications for the user.
    """
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read == False)
        .count()
    )

def mark_notification_read(db: Session, notification_id: str, user_id: str) -> bool:
    """
    Marks a single notification as read if owned by the user.
    """
    notif = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user_id)
        .first()
    )
    if not notif:
        return False
    notif.is_read = True
    db.commit()
    return True

def mark_all_notifications_read(db: Session, user_id: str) -> int:
    """
    Marks all notifications for the user as read.
    """
    updated = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read == False)
        .update({"is_read": True})
    )
    db.commit()
    return updated

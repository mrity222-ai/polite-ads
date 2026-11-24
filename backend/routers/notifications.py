import sys
from pathlib import Path
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database import get_db
from dependencies import require_active_user
from entities import User
from services.notifications import (
    get_user_notifications, get_unread_count,
    mark_notification_read, mark_all_notifications_read
)

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

@router.get("")
def list_notifications(
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Returns user's in-app notification list and unread count badge.
    """
    notifs = get_user_notifications(db, current_user.id)
    unread = get_unread_count(db, current_user.id)

    return {
        "unread_count": unread,
        "notifications": [
            {
                "id": n.id,
                "type": n.type,
                "title": n.title,
                "message": n.message,
                "is_read": n.is_read,
                "action_url": n.action_url,
                "created_at": n.created_at.isoformat()
            }
            for n in notifs
        ]
    }

@router.patch("/{notif_id}/read")
def read_notification(
    notif_id: str,
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Marks a single notification as read.
    """
    success = mark_notification_read(db, notif_id, current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found.")
    return {"status": "success", "id": notif_id}

@router.post("/mark-all-read")
def mark_all_read(
    current_user: User = Depends(require_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Marks all notifications for current user as read.
    """
    count = mark_all_notifications_read(db, current_user.id)
    return {"status": "success", "marked_read_count": count}

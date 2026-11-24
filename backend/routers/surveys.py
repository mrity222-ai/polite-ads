"""Authenticated, owner-scoped persistent ancillary requests. No WhatsApp automation."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from dependencies import require_active_user
from entities import User, ServiceRecord
from models import SurveyCreateRequest, ServiceRequest
router = APIRouter(prefix='/api/surveys', tags=['Surveys & Services'])

@router.get('/polls')
def get_active_polls(user: User = Depends(require_active_user), db: Session = Depends(get_db)):
    return [dict(id=row.id, **row.payload) for row in db.query(ServiceRecord).filter_by(user_id=user.id, kind='poll').all()]

@router.post('/create-poll')
def create_voter_poll(request: SurveyCreateRequest, user: User = Depends(require_active_user), db: Session = Depends(get_db)):
    if not request.question.strip() or not 2 <= len(request.options) <= 10 or any(not x.strip() for x in request.options):
        raise HTTPException(422, 'A question and 2–10 non-empty options are required.')
    payload = dict(question=request.question.strip(), options=[dict(label=x.strip(),percentage=0,votes=0) for x in request.options], total_votes=0)
    row = ServiceRecord(user_id=user.id, kind='poll', payload=payload)
    db.add(row); db.commit()
    return {'status':'success','poll':dict(id=row.id, **payload)}

@router.post('/request-service')
def request_campaign_service(request: ServiceRequest, user: User = Depends(require_active_user), db: Session = Depends(get_db)):
    if request.service_type not in ('video_reels', 'ground_survey'):
        raise HTTPException(422, 'Service unavailable. Automated political WhatsApp messaging is excluded.')
    row = ServiceRecord(user_id=user.id, kind='inquiry', payload=dict(service_type=request.service_type,note=request.note,status='Requested'))
    db.add(row);db.commit()
    return {'status':'success','request_id':row.id,'message':'Inquiry recorded; service delivery is not confirmed.'}

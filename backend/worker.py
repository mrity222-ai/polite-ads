"""Supervised queue worker with bounded leases, safe recovery and daily funding checks."""
import argparse
import time
from sqlalchemy import or_
from database import SessionLocal
from entities import PublishingJob
from services.publishing import execute_publishing_job, recover_expired, now_utc
from services.daily_funding import renew_due_campaigns


def run_once():
    with SessionLocal() as db:
        recover_expired(db)
        renew_due_campaigns(db)
        ids=[row.id for row in db.query(PublishingJob).filter(PublishingJob.status=='Queued',
            or_(PublishingJob.next_attempt_at.is_(None), PublishingJob.next_attempt_at<=now_utc())).order_by(PublishingJob.created_at).limit(25)]
        for job_id in ids:
            execute_publishing_job(db, job_id)
    return len(ids)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--once', action='store_true')
    parser.add_argument('--recover-mock', action='store_true', help='Compatibility flag: only expired leases are recovered automatically.')
    args=parser.parse_args()
    while True:
        run_once()
        if args.once:break
        time.sleep(2)

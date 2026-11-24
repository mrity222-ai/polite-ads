"""Create an administrator explicitly; password entered privately, never on the command line."""
import argparse
from getpass import getpass
from database import SessionLocal
from entities import User
from models import UserRegisterRequest
from security import hash_password

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--email',required=True)
    parser.add_argument('--mobile',required=True)
    parser.add_argument('--name',required=True)
    parser.add_argument('--username', default='super admin')
    parser.add_argument('--reset-existing', action='store_true', help='Rotate password for an existing administrator with this email.')
    args=parser.parse_args()
    password=getpass('Admin password (at least 8 characters): ')
    confirm=getpass('Confirm password: ')
    validated=UserRegisterRequest(full_name=args.name,mobile=args.mobile,email=args.email,password=password,confirm_password=confirm)
    if password != confirm:raise SystemExit('Passwords do not match.')
    with SessionLocal() as db:
        email=str(validated.email).lower().strip()
        username = args.username.strip().lower()
        if not username or len(username) > 100:
            raise SystemExit('Username must contain 1–100 characters.')
        username_owner = db.query(User).filter(User.username == username).first()
        if username_owner and username_owner.email != email:
            raise SystemExit('This private username is already assigned to another administrator.')
        if password in ('admin123', 'secret123', 'candidate123'):
            raise SystemExit('Choose a personal password; demo passwords are disabled.')
        existing = db.query(User).filter((User.email==email)|(User.mobile==validated.mobile)).first()
        if existing:
            if not args.reset_existing or existing.role != 'admin' or existing.email != email:
                raise SystemExit('Account exists; only an explicitly requested existing admin reset is allowed.')
            from security import revoke_all_user_sessions
            existing.password_hash = hash_password(password)
            existing.username = username
            existing.status = 'active'
            revoke_all_user_sessions(db, existing.id)
        else:
            db.add(User(full_name=validated.full_name,email=email,mobile=validated.mobile,username=username,password_hash=hash_password(password),role='admin',status='active'))
        db.commit()
    print('Administrator created. Password was not logged.')

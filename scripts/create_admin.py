"""
One-off script to promote/create an admin user.

Usage:
    cd backend
    python ../scripts/create_admin.py --email you@example.com --name "Admin" --password "SecurePass123"

If the email already exists, it's promoted to admin instead of erroring.
"""
import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.core.database import SessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402
from app.core.security import hash_password  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", default="Admin")
    parser.add_argument("--password", required=True)
    args = parser.parse_args()

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == args.email).first()
        if user:
            user.is_admin = True
            db.commit()
            print(f"Promoted existing user {args.email} to admin.")
        else:
            user = User(
                name=args.name, email=args.email,
                password_hash=hash_password(args.password), is_admin=True,
            )
            db.add(user)
            db.commit()
            print(f"Created new admin user {args.email}.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

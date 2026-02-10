"""
Promote a user to admin role.
Usage: python -m backend.scripts.promote_admin user@example.com
"""

import sys
import os

# Ensure parent directory is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.database import SessionLocal
from backend.models.user import User


def promote(email: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email.lower().strip()).first()
        if not user:
            print(f"User not found: {email}")
            return False
        if user.role == "admin":
            print(f"User {email} is already an admin.")
            return True
        user.role = "admin"
        db.commit()
        print(f"Promoted {email} ({user.full_name}) to admin.")
        return True
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m backend.scripts.promote_admin <email>")
        sys.exit(1)
    success = promote(sys.argv[1])
    sys.exit(0 if success else 1)

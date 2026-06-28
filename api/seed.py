import os
import sys

admin_path = os.path.join(os.path.dirname(__file__), "admin.txt")
flag_path = os.path.join(os.path.dirname(__file__), "seed_done.flag")
project_root = os.path.join(os.path.dirname(__file__), "..")

sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(__file__))

if not os.path.exists(admin_path):
    print("admin.txt not found — already seeded or never created.")
    open(flag_path, "w").close()
    sys.exit(0)

with open(admin_path) as f:
    creds = f.read().strip()

if ":" not in creds:
    print("admin.txt: invalid format — expected email:password")
    sys.exit(1)

email, password = creds.split(":", 1)

from database import init_db
from auth import create_user

init_db()

existing_user = __import__("auth", fromlist=["get_user_by_email"]).get_user_by_email(email)
if existing_user:
    print(f"Admin {email} already exists — skipping.")
else:
    from auth import hash_password
    from models import User, Wallet
    from database import SessionLocal
    db = SessionLocal()
    try:
        user = User(
            full_name="Admin",
            email=email,
            phone="0000000000",
            password_hash=hash_password(password),
            role="admin",
        )
        db.add(user)
        db.flush()
        wallet = Wallet(user_id=user.id, balance=0.00)
        db.add(wallet)
        db.commit()
        db.refresh(user)
        print(f"Admin {email} created successfully (id={user.id}).")
    finally:
        db.close()

os.remove(admin_path)
print(f"Deleted {admin_path}")

open(flag_path, "w").close()
print(f"Created {flag_path} — ready for cleanup.")

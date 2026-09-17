from sqlalchemy import select
from .config import settings
from .database import SessionLocal
from .models import Permission, Role, User
from .security import hash_password

ROLE_NAMES = ["SUPER_ADMIN", "ADMIN", "FRANCHISE_OWNER", "FRANCHISE_STAFF", "RESTAURANT_OWNER", "RESTAURANT_STAFF", "DELIVERY_PARTNER", "CUSTOMER"]

def seed():
    with SessionLocal() as db:
        roles = {}
        for name in ROLE_NAMES:
            role = db.scalar(select(Role).where(Role.name == name)) or Role(name=name, description=f"ParcelWalaa {name} role")
            db.add(role); roles[name] = role
        db.flush()
        user = db.scalar(select(User).where(User.email == settings.seed_admin_email.lower()))
        if not user:
            user = User(email=settings.seed_admin_email.lower(), full_name="ParcelWalaa Administrator", password_hash=hash_password(settings.seed_admin_password), roles=[roles["SUPER_ADMIN"]])
            db.add(user)
        elif roles["SUPER_ADMIN"] not in user.roles:
            user.roles.append(roles["SUPER_ADMIN"])
        db.commit()
        print(f"Seeded {settings.seed_admin_email}")

if __name__ == "__main__": seed()

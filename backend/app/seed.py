from sqlalchemy import select

from app.config import settings
from app.database import SessionLocal
from app.models import Role, User
from app.security import hash_password

ROLE_NAMES = [
    "SUPER_ADMIN",
    "ADMIN",
    "FRANCHISE_OWNER",
    "FRANCHISE_STAFF",
    "RESTAURANT_OWNER",
    "RESTAURANT_STAFF",
    "DELIVERY_PARTNER",
    "CUSTOMER",
]


def seed_roles(db):
    roles = {}
    for name in ROLE_NAMES:
        role = db.scalar(select(Role).where(Role.name == name))
        if not role:
            role = Role(name=name, description=f"ParcelWalaa {name} role")
            db.add(role)
        roles[name] = role
    db.flush()
    return roles


def seed():
    with SessionLocal() as db:
        roles = seed_roles(db)
        user = db.scalar(select(User).where(User.email == settings.seed_admin_email.lower()))

        if not user:
            user = User(
                email=settings.seed_admin_email.lower(),
                full_name="ParcelWalaa Administrator",
                password_hash=hash_password(settings.seed_admin_password),
                roles=[roles["SUPER_ADMIN"]],
            )
            db.add(user)
        elif "SUPER_ADMIN" not in {role.name for role in user.roles}:
            user.roles.append(roles["SUPER_ADMIN"])

        db.commit()
        print(f"Seeded super admin: {settings.seed_admin_email}")
        print(f"Seeded roles: {', '.join(ROLE_NAMES)}")


if __name__ == "__main__":
    seed()

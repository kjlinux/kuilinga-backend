"""Create a test user for logout testing"""
from app.db.session import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash
from app.models.organization import Organization

db = SessionLocal()

try:
    # Check if organization exists
    org = db.query(Organization).first()
    if not org:
        org = Organization(
            name="Test Organization",
            email="test@test.com",
            phone="1234567890"
        )
        db.add(org)
        db.commit()
        db.refresh(org)
        print(f"Created organization: {org.name}")

    # Check if user exists
    user = db.query(User).filter(User.email == "test@test.com").first()

    if not user:
        user = User(
            email="test@test.com",
            full_name="Test User",
            hashed_password=get_password_hash("test123"),
            is_active=True,
            is_superuser=True,
            organization_id=org.id
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Created user: {user.email} with password: test123")
    else:
        print(f"User already exists: {user.email}")

except Exception as e:
    print(f"Error: {e}")
    db.rollback()
finally:
    db.close()

from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.db.models.audit_log import AuditLog  # noqa: F401
from app.db.models.email_outbox import EmailOutbox  # noqa: F401
from app.db.models.favorite import Favorite  # noqa: F401
from app.db.models.inquiry import Inquiry  # noqa: F401
from app.db.models.inquiry_message import InquiryMessage  # noqa: F401
from app.db.models.listing import Listing  # noqa: F401
from app.db.models.payment_log import PaymentLog  # noqa: F401
from app.db.models.rate_limit_event import RateLimitEvent  # noqa: F401
from app.db.models.reservation import Reservation  # noqa: F401
from app.db.models.search_log import SearchLog  # noqa: F401
from app.db.models.two_factor_challenge import TwoFactorChallenge  # noqa: F401
from app.db.models.user import User  # noqa: F401
from app.db.models.viewing import Viewing  # noqa: F401
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.web.auth import hash_password


def _seed_default_admin() -> None:
    if not settings.seed_default_admin:
        return
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "admin").first()
        if existing is None:
            existing = db.query(User).filter(User.email == "admin@homefinder.com").first()
        if existing is not None:
            existing.role = "admin"
            existing.email_verified = True
            if not str(existing.email).endswith(".local"):
                existing.must_reset_password = True
            if "@" not in str(existing.email):
                existing.email = "admin@homefinder.com"
            db.add(existing)
            db.commit()
            return
        admin_user = User(
            email="admin@homefinder.com",
            username="admin",
            password=hash_password("admin"),
            role="admin",
            email_verified=True,
            must_reset_password=True,
        )
        db.add(admin_user)
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.query(User).filter(User.username == "admin").first()
        if existing is not None:
            existing.role = "admin"
            existing.email_verified = True
            existing.must_reset_password = True
            db.add(existing)
            db.commit()
    finally:
        db.close()


def _seed_demo_supervisor() -> None:
    if not settings.seed_default_admin:
        return
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "supervisor").first()
        if existing is None:
            existing = db.query(User).filter(User.email == "supervisor@homefinder.local").first()
        if existing is not None:
            existing.email = "supervisor@homefinder.local"
            existing.role = "service_supervisor"
            existing.email_verified = True
            existing.must_reset_password = False
            db.add(existing)
            db.commit()
            return
        supervisor_user = User(
            email="supervisor@homefinder.local",
            username="supervisor",
            password=hash_password("Supervisor123"),
            role="service_supervisor",
            email_verified=True,
            must_reset_password=False,
        )
        db.add(supervisor_user)
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.query(User).filter(User.username == "supervisor").first()
        if existing is not None:
            existing.role = "service_supervisor"
            existing.email_verified = True
            existing.must_reset_password = False
            db.add(existing)
            db.commit()
    finally:
        db.close()


def init_db() -> None:
    """Create all tables if they don't exist, then seed initial data."""
    Base.metadata.create_all(bind=engine)
    InquiryMessage.__table__.create(bind=engine, checkfirst=True)
    _seed_default_admin()
    _seed_demo_supervisor()

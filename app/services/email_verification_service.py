from app.core.config import settings
from app.services.email_service import EmailMessage, send_email
from app.services.user_service import generate_email_verification_token


def send_verification_email(email: str) -> None:
    token = generate_email_verification_token(email)
    verify_url = f"{settings.public_base_url}/verify-email?token={token}"
    send_email(
        EmailMessage(
            to=email,
            subject="Verify your HomeFinder email",
            body=(
                "Welcome to HomeFinder.\n\n"
                f"Verify your email by opening this link:\n{verify_url}\n\n"
                "If you did not register, you can ignore this email."
            ),
        )
    )

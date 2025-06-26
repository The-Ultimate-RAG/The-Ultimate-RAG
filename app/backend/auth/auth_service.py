import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from secrets import token_urlsafe

from sympy.liealgebras.type_e import TypeE
from app.backend.auth.utils import hash_access_string, create_access_token
from app.backend.models.users import UserController, User, UserAlreadyExistsError, UserNotFoundError
from utils import hash_password, create_access_string, verify_password
import jwt
from datetime import datetime, timedelta
from app.settings import settings
from email_config import EmailConfig


class AuthService:
    def __init__(self, user_controller: UserController):
        if not isinstance(user_controller, UserController):
            raise TypeError("user_controller must be an instance of UserController class")
        self.users = user_controller

    def register_user(self, email: str, password: str) -> tuple[User, str]:
        """Register a new user and return the user and a new access token."""
        try:
            password_hashed = hash_password(password)
            access_string = create_access_string()
            access_string_hashed = hash_access_string(access_string)

            new_user = self.users.add_new_user(email=email,
                                               password_hash=password_hashed,
                                               access_string_hash=access_string_hashed
                                               )

            access_token = create_access_token(access_string)
            return new_user, access_token

        except UserAlreadyExistsError:
            raise UserAlreadyExistsError(f"User with email {email} already exists.")

    def authenticate_user(self, email: str, password: str) -> tuple[User, str]:
        """Authenticate a new user and return the user and a new access token."""
        user = self.users.find_user_by_email(email=email)
        if not user or not verify_password(password, user.password_hash):
            raise AuthorizationError("Invalid email or password")

        access_string = create_access_string()
        access_string_hashed = hash_access_string(access_string)
        self.users.update_user(user_id=user.id, access_string_hash=access_string_hashed)
        access_token = create_access_token(access_string)
        return user, access_token

    def get_user_from_token(self, token: str):
        try:
            payload = jwt.decode(token, settings.secret_pepper, algorithms=[settings.jwt_algorithm])
            access_string = payload.get('access_string_hash')
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
            return None

        if not access_string:
            return None

        return self.users.find_user_by_access_string(hash_access_string(access_string))

    def request_password_reset(self, email: str, expires_delta=settings.password_reset_token_lifetime):
        user = self.users.find_user_by_email(email=email)
        if not user:
            logging.warning(f"Password reset requested for non-existent email: {email}")
            return

        expires_at = datetime.now() + expires_delta
        reset_token = token_urlsafe(32)
        hashed_reset_token = hash_access_string(reset_token)

        self.users.update_user(
            user_id=user.id,
            reset_password_hash=hashed_reset_token,
            reset_token_expires_at=expires_at
        )

        self._send_password_reset_email(email, reset_token, expires_delta)

    @staticmethod
    def _send_password_reset_email(receiver_email: str, reset_token: str,
                                   expires_delta: timedelta = settings.password_reset_token_lifetime,
                                   config: EmailConfig = None):
        if config is None:
            config = EmailConfig.from_env()

        message = MIMEMultipart("alternative")
        message["Subject"] = "Password Reset Request"
        message["From"] = config.smtp_email
        message["To"] = receiver_email

        with open("../../email_templates/password_reset.html", "r", encoding="utf-8") as email_template:
            html_template = email_template.read()

        expires_in = int(expires_delta.total_seconds() / 60)

        text = html_template.format(application_server_url=config.application_server_url,
                                    reset_token=reset_token,
                                    expires_in=expires_in
                                    )

        message.attach(MIMEText(text, "html"))

        context = ssl.create_default_context()
        with smtplib.SMTP(config.smtp_host, config.smtp_port) as server:
            server.starttls(context=context)
            server.login(config.smtp_email, config.smtp_password)
            server.sendmail(config.smtp_email, receiver_email, message.as_string())




if __name__ == "__main__":
    AuthService._send_password_reset_email("mnogoboksov21@gmail.com", "jdlksafj", timedelta(hours=1))


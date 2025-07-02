import logging
from datetime import datetime
from typing import Optional
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session

from app.backend.schemas import LanguageOptions, ThemeOptions
from app.backend.exceptions import (
    DatabaseError,
    UserNotFoundError,
    UserAlreadyExistsError,
)
from app.backend.models.users import User


class UserController:
    def __init__(self, database_session: Session):
        self.database = database_session

    @staticmethod
    def _execute_query(query) -> Optional[User]:
        """
        Helper method to execute a query and handle common database errors.
        """
        try:
            return query.first()
        except SQLAlchemyError as e:
            logging.error(f"Database error during user query: {e}", exc_info=True)
            raise DatabaseError(f"Failed to query user due to a database error: {e}")

    def add_new_user(
        self, email: str, password_hash: str, access_string_hash: str
    ) -> User:
        if self.find_user_by_email(email):
            logging.warning(f"Attempted to register existing email: {email}")
            raise UserAlreadyExistsError(f"User with email {email} already registered")

        new_user = User(
            email=email,
            password_hash=password_hash,
            access_string_hash=access_string_hash,
        )

        self.database.add(new_user)

        try:
            self.database.commit()
            self.database.refresh(new_user)
            logging.info(f"Successfully registered new user: {new_user}")
            return new_user
        except IntegrityError as e:
            self.database.rollback()
            logging.error(
                f"Integrity error when adding user '{email}': {e}", exc_info=True
            )
            raise UserAlreadyExistsError(f"User with email {email} already exists")
        except SQLAlchemyError as e:
            self.database.rollback()
            raise DatabaseError(f"Failed to add new user due to a database error: {e}")

    def find_user_by_id(self, user_id: int) -> User | None:
        query = self.database.query(User).filter(User.id == user_id)
        return self._execute_query(query)

    def find_user_by_email(self, email: str) -> User | None:
        query = self.database.query(User).filter(User.email == email)
        return self._execute_query(query)

    def find_user_by_access_string(self, access_string_hash: str) -> User | None:
        query = self.database.query(User).filter(
            User.access_string_hash == access_string_hash
        )
        return self._execute_query(query)

    def update_user(self, user_id: int, **kwargs) -> User:
        user_to_update = self.find_user_by_id(user_id)

        if not user_to_update:
            raise UserNotFoundError("User not found")

        allowed_updates = {
            "language": LanguageOptions,
            "theme": ThemeOptions,
            "access_string_hash": str,
            "password_hash": str,
            "reset_token_expires_at": datetime,
        }

        for key, value in kwargs.items():
            if key in allowed_updates:
                expected_type = allowed_updates[key]
                if not isinstance(value, expected_type) or value is None:
                    raise ValueError(
                        f"Invalid type for {key}. Expected {expected_type}, got {type(value).__name__}"
                    )

                setattr(user_to_update, key, value)
            else:
                logging.warning(
                    f"Attempted to updated disallowed key: {key} for user {user_id}. Ignoring"
                )

        try:
            self.database.commit()
            self.database.refresh(user_to_update)
            logging.info(f"Successfully updated user: {user_to_update}")
            return user_to_update
        except SQLAlchemyError as e:
            logging.error(
                f"Failed to update user ID {user_id} due to a database error: {e}",
                exc_info=True,
            )
            raise DatabaseError(f"Failed to update user due to a database error: {e}")

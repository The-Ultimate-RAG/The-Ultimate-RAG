from fastapi import Response, HTTPException
from app.backend.models.users import User, find_user_by_email, add_new_user, update_user
from app.backend.controllers.users import (
    create_access_string,
    hash_access_string,
    create_access_token,
)
from app.settings import settings
from bcrypt import gensalt, hashpw


def login_as_admin(response: Response):
    """
    Handles the authentication for the admin user.

    This function is called when a user tries to log in with 'admin' credentials.
    If the admin user does not exist in the database, it will be created with
    the password 'admin'.

    It then generates a session token and sets it as a cookie to log the user in.
    """
    admin_email = "admin"
    admin_pass = "admin"

    try:
        # Find the admin user by email
        user: User = find_user_by_email(email=admin_email)

        # If the admin user doesn't exist, create one
        if not user:
            # Generate a salt and hash the admin password
            salt: bytes = gensalt(rounds=16)
            password_hashed: str = hashpw(admin_pass.encode("utf-8"), salt).decode(
                "utf-8"
            )

            # An access string is used for session management.
            access_string: str = create_access_string()
            access_string_hashed: str = hash_access_string(string=access_string)

            # Add the new admin user to the database
            add_new_user(
                email=admin_email,
                password_hash=password_hashed,
                access_string_hash=access_string_hashed,
            )

            # Retrieve the newly created user to proceed
            user = find_user_by_email(email=admin_email)

        # At this point, the admin user is guaranteed to exist.
        # We don't need to re-check the password because this function is only
        # called after the credentials have been verified in the API endpoint.

        # Generate a new access string and token for the session
        access_string: str = create_access_string()
        access_string_hashed: str = hash_access_string(string=access_string)
        update_user(user, access_string_hash=access_string_hashed)
        access_token = create_access_token(access_string)

        # Set the access token in an HTTPOnly cookie for security
        response.set_cookie(
            key="access_token",
            value=access_token,
            path="/",
            max_age=settings.max_cookie_lifetime,
            httponly=True,
        )

        return {"status": "ok", "message": "Admin logged in successfully"}

    except Exception as e:
        # In case of any database or other errors, return a server error
        print(f"Error during admin login: {e}")
        raise HTTPException(
            status_code=500, detail="An internal error occurred during admin login."
        )

import getpass
import sys
from pathlib import Path

# Add the project root to the Python path to allow for absolute imports
# This assumes the script is run from the directory where create_admin.py is located
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from app.backend.models.base_model import Base
from app.backend.controllers.base_controller import engine
from app.backend.models.users import User, add_new_user, find_user_by_email
from app.backend.models.chats import Chat  # Import Chat to ensure it's registered with Base metadata
from app.backend.auth.utils import hash_password

def create_admin_user():
    """
    Creates an admin user by prompting for an email and password from the command line.
    """
    print("--- Create Admin User ---")

    # Ensure all tables are created in the database
    # Importing User and Chat models ensures they are registered with Base.metadata
    Base.metadata.create_all(bind=engine)
    print("Database tables checked/created.")

    email = input("Enter admin email: ")

    if find_user_by_email(email):
        print(f"\nError: User with email '{email}' already exists.")
        return

    password = getpass.getpass("Enter admin password: ")
    password_confirm = getpass.getpass("Confirm admin password: ")

    if password != password_confirm:
        print("\nError: Passwords do not match.")
        return

    # Note: The password 'admin' does not meet the complexity requirements in schemas.py.
    # This script bypasses the Pydantic validation, but for a production environment,
    # a strong password should be used.
    if password == "admin":
        print("\nWarning: The password 'admin' is insecure and does not meet the application's defined security policies.")
        proceed = input("Are you sure you want to continue with this password? (y/n): ")
        if proceed.lower() != 'y':
            print("Admin user creation cancelled.")
            return

    # Hash the password before storing it
    password_hash = hash_password(password)

    # Add the new user to the database
    # The 'access_string_hash' is nullable and can be set to None
    add_new_user(email=email, password_hash=password_hash, access_string_hash=None)

    print(f"\nAdmin user '{email}' was created successfully.")


if __name__ == "__main__":
    create_admin_user()
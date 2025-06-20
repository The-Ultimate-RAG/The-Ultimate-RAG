from app.backend.models.users import User
from app.backend.models.chats import new_chat

def create_new_chat(title: str | None, user: User) -> str:
    return f"/chats/id={new_chat(title, user)}"
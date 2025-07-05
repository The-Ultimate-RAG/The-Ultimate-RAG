from app.backend.models.messages import get_messages_by_chat_id, Message
from app.backend.models.users import User, get_user_chats
from app.backend.controllers.utils import get_group_title
from app.settings import BASE_DIR
from app.backend.models.chats import (
    get_chats_by_user_id,
    get_chat_by_id,
    refresh_title,
    add_new_chat,
)

from datetime import datetime, timedelta
from fastapi import HTTPException
from uuid import uuid4
import os


def create_new_chat(title: str | None, user: User) -> dict:
    print("+" * 40, "START Creating Chat", "+" * 40)
    try:
        chat_id = str(uuid4())
        add_new_chat(id=chat_id, title=title, user=user)
        try:
            path_to_chat = os.path.join(
                BASE_DIR,
                "chats_storage",
                f"user_id={user.id}",
                f"chat_id={chat_id}",
                "documents",
            )
            os.makedirs(path_to_chat, exist_ok=True)
        except Exception:
            raise HTTPException(500, "error while creating chat folders")

        return {"url": f"/chats/id={chat_id}", "chat_id": chat_id}
    except Exception as exception:
        raise exception
    finally:
        print("+" * 40, "END Creating Chat", "+" * 40, "\n\n")


def dump_messages_dict(messages: list[Message], dst: dict) -> None:
    history = []

    print("!" * 40, "START Dumping History", "!" * 40)
    for message in messages:
        history.append({"role": message.sender, "content": message.content})
        print(f"Role ----> {message.sender}, Content ----> {message.content}\n")
    print("!" * 40, "END Dumping History", "!" * 40, "\n\n")

    dst.update({"history": history})


def get_chat_with_messages(id: str) -> dict:
    response = {"chat_id": id}

    chat = get_chat_by_id(id=id)
    if chat is None:
        raise HTTPException(418, f"Invalid chat id. Chat with id={id} does not exists!")

    messages = get_messages_by_chat_id(id=id)
    dump_messages_dict(messages, response)

    return response


def create_dict_from_chat(chat) -> dict:
    return {"id": chat.id, "title": chat.title}


def list_user_chats(user_id: str) -> list[dict]:
    current_date = datetime.now()

    today = []
    last_week = []
    last_month = []
    later = []

    groups = [today, last_week, last_month, later]

    chats = get_chats_by_user_id(user_id)
    for chat in chats:
        if current_date - timedelta(days=1) <= chat.created_at:
            today.append(chat)
        elif current_date - timedelta(weeks=1) <= chat.created_at:
            last_week.append(chat)
        elif current_date - timedelta(weeks=4) <= chat.created_at:
            last_month.append(chat)
        else:
            later.append(chat)

    result = []

    for id, group in enumerate(groups):
        if len(group):
            result.append(
                {"title": get_group_title(id=id), "chats": [create_dict_from_chat(chat) for chat in group]}
            )

    return result


def verify_ownership_rights(user: User, chat_id: str) -> bool:
    return chat_id in [chat.id for chat in get_user_chats(user)]


def update_title(chat_id: str) -> bool:
    return refresh_title(chat_id)

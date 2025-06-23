from app.backend.models.users import User, get_user_chats
from app.backend.models.chats import new_chat, get_chat_by_id, get_chats_by_user_id, refresh_title, Chat
from app.backend.models.messages import get_messages_by_chat_id, Message
from fastapi import HTTPException
from datetime import datetime, timedelta

def create_new_chat(title: str | None, user: User) -> str:
    return f"/chats/id={new_chat(title, user)}"

def dump_messages_dict(messages: list[Message], dst: dict) -> None:
    history = []

    for message in messages:
        history.append(
            {
                "role": message.sender,
                "content": message.content
            }
        )

    dst.update({"history": history})


def get_chat_with_messages(id: int) -> dict:
    response = {"chat_id": id}

    chat = get_chat_by_id(id=id)
    if chat is None:
        raise HTTPException(418, f"Invalid chat id. Chat with id={id} does not exists!")
    
    messages = get_messages_by_chat_id(id=id)
    dump_messages_dict(messages, response)

    return response


def create_dict_from_chat(chat) -> dict:
    return {
        "id": chat.id,
        "title": chat.title
    }


def list_user_chats(user_id: int) -> list[dict]:
    current_date = datetime.now()

    today = []
    last_week = []
    last_month = []
    other = []

    chats = get_chats_by_user_id(user_id)
    for chat in chats:
        if current_date - timedelta(days=1) <= chat.created_at:
            today.append(chat)
        elif current_date - timedelta(weeks=1) <= chat.created_at:
            last_week.append(chat)
        elif current_date - timedelta(weeks=4) <= chat.created_at:
            last_month.append(chat)
        else:
            other.append(chat)

    result = []

    # da da eto ochen ploho ...
    if len(today):
        result.append({"title": "TODAY", "chats":[create_dict_from_chat(chat) for chat in today]})
    if len(last_week):
        result.append({"title": "LAST WEEK", "chats":[create_dict_from_chat(chat) for chat in last_week]})
    if len(last_month):
        result.append({"title": "LAST MONTH", "chats":[create_dict_from_chat(chat) for chat in last_month]})
    if len(other):
        result.append({"title": "LATER", "chats":[create_dict_from_chat(chat) for chat in other]})

    return result


def verify_ownership_rights(user: User, chat_id: int) -> bool:
    return chat_id in [chat.id for chat in get_user_chats(user)]
        

def update_title(chat_id: int) -> bool:
    return refresh_title(chat_id)
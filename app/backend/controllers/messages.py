from app.backend.models.messages import new_message

def register_message(content: str, sender: str, chat_id: int) -> None:
    return new_message(chat_id=chat_id, sender=sender, content=content)
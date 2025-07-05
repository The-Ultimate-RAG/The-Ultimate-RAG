from app.backend.models.messages import add_new_message
from uuid import uuid4
import re


def remove_html_tags(content: str) -> str:
    pattern = "<(.*?)>"
    replace_with = (
        "<a href=https://www.youtube.com/results?search_query=rickroll>click me</a>"
    )
    de_taggeed = re.sub(pattern, "REPLACE_WITH_RICKROLL", content)

    return de_taggeed.replace("REPLACE_WITH_RICKROLL", replace_with)


def register_message(content: str, sender: str, chat_id: str) -> None:
    print("-" * 40, "START Registering Message", "-" * 40)
    try:
        id = str(uuid4())
        message = content if sender == "assistant" else remove_html_tags(content)

        print(f"Message -----> {message[:min(30, len(message))]}")

        return add_new_message(id=id, chat_id=chat_id, sender=sender, content=message)
    finally:
        print("-" * 40, "END Registering Message", "-" * 40, "\n\n")

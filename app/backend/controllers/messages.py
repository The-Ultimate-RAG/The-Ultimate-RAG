from app.backend.models.messages import add_new_message
from app.settings import settings, logger
from uuid import uuid4
import asyncio
import re


async def remove_html_tags(content: str) -> str:
    loop = asyncio.get_event_loop()
    def strip_tags():
        pattern = "<(.*?)>"
        replace_with = (
            "<a href=https://www.youtube.com/results?search_query=rickroll>click me</a>"
        )
        de_taggeed = re.sub(pattern, "REPLACE_WITH_RICKROLL", content)

        return de_taggeed.replace("REPLACE_WITH_RICKROLL", replace_with)
    return await loop.run_in_executor(None, strip_tags)


async def register_message(content: str, sender: str, chat_id: str) -> None:
    if settings.debug:
        await logger.info("START Registering Message")
    try:
        id = str(uuid4())
        message = content if sender == "assistant" else await remove_html_tags(content)

        if settings.debug:
            await logger.info(f"Message -----> {message[:min(30, len(message))]}")

        return await add_new_message(id=id, chat_id=chat_id, sender=sender, content=message)
    finally:
        if settings.debug:
            await logger.info("END Registering Message")

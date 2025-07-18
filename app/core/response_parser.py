from app.core.document_validator import path_is_valid
import asyncio
import re


def create_url(match: re.Match) -> str:
    path: str = match.group(1)
    page: str = match.group(2)
    lines: str = match.group(3)
    start: str = match.group(4)

    if not path_is_valid(path):
        return "###NOT VALID PATH###"

    return f'<a href="/viewer?path={path}&page={page}&lines={lines}&start={start}">[Source]</a>'


async def add_links(response: str) -> str:
    citation_format = r"\[Source:\s*([^,]+?)\s*,\s*Page:\s*(\d+)\s*,\s*Lines:\s*(\d+\s*-\s*\d+)\s*,\s*Start:?\s*(\d+)\]"
    return await asyncio.to_thread(re.sub, citation_format, create_url, response)

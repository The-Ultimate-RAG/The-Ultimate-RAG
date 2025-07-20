import re

"""
Replaces the matched regular exp with link via html <a></a>
"""


def create_url(match: re.Match) -> str:
    path: str = match.group(1)
    page: str = match.group(2)
    lines: str = match.group(3)
    start: str = match.group(4)

    return f'<a href="{path}">[Source]</a>'


"""
Replaces all occurrences of citation pattern with links
"""


def add_links(response: str) -> str:

    citation_format = r"\[Source:\s*([^,]+?)\s*,\s*Page:\s*(\d+)\s*,\s*Lines:\s*(\d+\s*-\s*\d+)\s*,\s*Start:?\s*(\d+)\]"
    return re.sub(pattern=citation_format, repl=create_url, string=response)

print(add_links(r"[Source: C:\Users\User\mine\code\The-Ultimate-RAG\chats_storage\user_id=8b1be678-f2c7-4a63-b110-7627af9b1cf8\chat_id=d889d8dd-f74c-4b33-a214-d6c69b68eb98\documents\pdfs\7e2b5257-5261-4100-ae65-488e06af2e25.pdf, Page: 18, Lines: 1-2, Start: 0]"))
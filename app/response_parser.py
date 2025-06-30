import re

from app.document_validator import path_is_valid

"""
Replaces the matched regular exp with link via html <a></a>
"""


def create_url(match: re.Match) -> str:
    path: str = match.group(1)
    page: str = match.group(2)
    lines: str = match.group(3)
    start: str = match.group(4)

    if not path_is_valid(path):
        return ""

    return f'<a href="/viewer?path={path}&page={page}&lines={lines}&start={start}">[Source]</a>'


"""
Replaces all occurrences of citation pattern with links
"""


def add_links(response: str) -> str:

    citation_format = r"\[Source:\s*([^,]+?)\s*,\s*Page:\s*(\d+)\s*,\s*Lines:\s*(\d+\s*-\s*\d+)\s*,\s*Start:?\s*(\d+)\]"
    return re.sub(pattern=citation_format, repl=create_url, string=response)

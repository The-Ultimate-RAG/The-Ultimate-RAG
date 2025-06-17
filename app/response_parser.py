from document_validator import path_is_valid
import re

def create_url(match) -> str:
    path = match.group(1)
    page = match.group(2)
    lines = match.group(3)
    start = match.group(4)

    if not path_is_valid(path):
        return ""
    
    return f'<a href="/viewer?path={path}&page={page}&lines={lines}&start={start}">[Source]</a>'


def add_links(response: str) -> str:
    citation_format = r'\[Source:\s*([^,]+?)\s*,\s*Page:\s*(\d+)\s*,\s*Lines:\s*(\d+\s*-\s*\d+)\s*,\s*Start:?\s*(\d+)\]'

    return re.sub(citation_format, create_url, response)

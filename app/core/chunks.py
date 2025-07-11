import uuid


class Chunk:
    """
    id -> unique number in uuid format, can be tried https://www.uuidgenerator.net/
    start_index -> the index of the first char from the beginning of the original document

    TODO: implement access modifiers and set of getters and setters
    """

    def __init__(
        self,
        id: uuid.UUID,
        filename: str,
        page_number: int,
        start_index: int,
        start_line: int,
        end_line: int,
        text: str,
    ):
        self.id: uuid.UUID = id
        self.filename: str = filename
        self.page_number: int = page_number
        self.start_index: int = start_index
        self.start_line: int = start_line
        self.end_line: int = end_line
        self.text: str = text

    async def get_raw_text(self) -> str:
        return self.text

    async def get_splitted_text(self) -> list[str]:
        return self.text.split(" ")

    async def get_metadata(self) -> dict:
        return {
            "id": str(self.id),
            "filename": self.filename,
            "page_number": self.page_number,
            "start_index": self.start_index,
            "start_line": self.start_line,
            "end_line": self.end_line,
        }

    async def __str__(self):
        return (
            f"Chunk from {self.filename.split('/')[-1]}, "
            f"page - {self.page_number}, "
            f"start - {self.start_line}, "
            f"end - {self.end_line}, "
            f"and text - {self.text[:100]}... ({len(self.text)})...{self.text[-20:]}\n"
        )

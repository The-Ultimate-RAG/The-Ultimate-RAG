class Chunk:
    def __init__(self, id: int, filename: str, page_number: int, start_index: int, start_line: int, end_line: int, text: str):
        self.id = id
        self.filename = filename
        self.page_number = page_number
        self.start_index = start_index
        self.start_line = start_line
        self.end_line = end_line
        self.text = text


    def get_raw_text(self) -> str:
        return self.text
    

    def get_metadata(self) -> dict:
        return {
            "id": self.id,
            "filename": self.filename,
            "page_number": self.page_number,
            "start_line": self.start_line,
            "end_line": self.end_line,
        }
    

    #TODO: remove kostyly
    def __str__(self):
        return f"Chunk from {self.filename.split("/")[-1]}, page - {self.page_number}, start - {self.start_line}, end - {self.end_line}, and text - {self.text[:100]}...({len(self.text)})"
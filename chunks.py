import uuid

class Chunk:
    '''
    TODO: implement access modifiers and set of getters and setters
    '''
    def __init__(self, id: uuid.UUID, filename: str, page_number: int, start_index: int, start_line: int, end_line: int, text: str):
        self.id: uuid.UUID = id
        self.filename: str = filename
        self.page_number: int = page_number
        self.start_index: int = start_index
        self.start_line: int = start_line
        self.end_line: int = end_line
        self.text: str = text


    def get_raw_text(self) -> str:
        return self.text
    

    def get_splitted_text(self) -> list[str]:
        return self.text.split(" ")
    
    
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
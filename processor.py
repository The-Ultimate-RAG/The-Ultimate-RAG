from langchain_community.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader, TextLoader # Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from chunks import Chunk

import logging

# TODO: add requirements.txt

class document_processor:

    '''
    chunks -> the list of chunks from loaded files
    processed -> the list of files that were already splitted into chunks
    upprocessed -> !processed
    text_splitter -> text splitting strategy
    '''
    def __init__(self):
        self.chunks: list[Chunk] = []
        self.processed: list[Document] = []
        self.unprocessed: list[Document] = []
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,
            chunk_overlap=70,
            length_function=len,
            is_separator_regex=False,
            add_start_index=True,
        )


    '''
    Loads one file - extracts text from file

    TODO: Consider AzureAIDocumentIntelligenceLoader
    TODO: Replace UnstructuredWordDocumentLoader with Docx2txtLoader
    TODO: Play with .pdf and text from img extraction

    add_to_unprocessed -> used to add loaded file to the list of unprocessed(unchunked) files if true
    '''
    def load_document(self, filepath: str, add_to_unprocessed: bool = False) -> list[Document]:
        loader = None

        if filepath.endswith(".pdf"):
            loader = PyPDFLoader(file_path=filepath) # splits each presentation into slides and processes it as separate file
        elif filepath.endswith(".docx"):
            # loader = Docx2txtLoader(file_path=filepath) ## try it later
            loader = UnstructuredWordDocumentLoader(file_path=filepath)
        elif filepath.endswith(".txt"):
            loader = TextLoader(file_path=filepath)

        if loader is None:
            raise RuntimeError("Unsupported type of file")
        
        documents: list[Document] = [] # We can not assign a single value to the document since .pdf are splitted into several files
        try:
            documents = loader.load()
        except Exception:
            raise RuntimeError("File is currpted")
        
        if add_to_unprocessed:
            for doc in documents:
                self.unprocessed.append(doc)

        return documents
    

    '''
    Similar to load_document, but for multiple files

    add_to_unprocessed -> used to add loaded files to the list of unprocessed(unchunked) files if true
    '''
    def load_documents(self, documents: list[str], add_to_unprocessed: bool = False) -> list[Document]:
        exctracted_documents: list[Document] = []

        for doc in documents:
            temp_storage: list[Document] = []

            try:
                temp_storage = self.load_document(filepath=doc, add_to_unprocessed=False) # In some cases it should be True, but i can not imagine any :(
            except Exception as e:
                logging.error("Error at load_documents while loading %s", doc, exc_info=e)
                continue
            
            for extrc_doc in temp_storage:
                exctracted_documents.append(extrc_doc)

                if add_to_unprocessed:
                    self.unprocessed.append(extrc_doc)

        return exctracted_documents
    

    '''
    Generates chunks with recursive splitter from the list of unprocessed files, add files to the list of processed, and clears unprocessed
    '''
    def generate_chunks(self):
        for document in self.unprocessed:
            self.processed.append(document)

            text: list[str] = self.text_splitter.split_documents([document])

            for chunk in text:

                # TODO: fix indexing
                start_l, end_l = self.get_start_end_lines(
                    text=chunk.page_content,
                    start_char=chunk.metadata["start_index"],
                    end_char=chunk.metadata["start_index"] + len(chunk.page_content)
                )

                self.chunks.append(Chunk(
                    id=len(self.chunks),
                    filename=document.metadata.get("source", ""),
                    page_number=document.metadata.get("page", 0),
                    start_index=chunk.metadata["start_index"],
                    start_line=start_l,
                    end_line=end_l,
                    text=chunk.page_content
                ))


    '''
    Some magic stuff here. To be honest, i understood it after 7th attempt
    '''
    def get_start_end_lines(self, text: str, start_char: int, end_char: int) -> list[int]: # TODO: add better function return value description
        lines = text.split("\n")
        start, end, char_ct = 0, 0, 0

        for i, line in enumerate(lines):
            if char_ct <= start_char <= char_ct + len(line) + 1:
                start = i + 1
            if char_ct <= end_char <= char_ct + len(line) + 1:
                end = i + 1
                break
            char_ct += len(line) + 1

        return start, end

  
if __name__ == "__main__":
    processor = document_processor()
    processor.load_documents([
        "/your local path/sample.docx",
        "/your local path/sample.txt",
        "/your local path/sample.pdf"
        ], add_to_unprocessed=True)
    processor.generate_chunks()

    for c in processor.chunks:
        print(c)
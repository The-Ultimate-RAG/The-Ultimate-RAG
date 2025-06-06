from langchain_community.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from chunks import Chunk
import nltk

# TODO: create some config file with debug_mode, logger config and further stuff

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
    handlers=[logging.StreamHandler()]
)

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

    TODO: Replace UnstructuredWordDocumentLoader with Docx2txtLoader
    TODO: Play with .pdf and text from img extraction
    TODO: Try chunking with llm

    add_to_unprocessed -> used to add loaded file to the list of unprocessed(unchunked) files if true
    '''
    def load_document(self, filepath: str, add_to_unprocessed: bool = False) -> list[Document]:
        loader = None

        if filepath.endswith(".pdf"):
            loader = PyPDFLoader(file_path=filepath) # splits each presentation into slides and processes it as separate file
        elif filepath.endswith(".docx") or filepath.endswith(".doc"):
            # loader = Docx2txtLoader(file_path=filepath) ## try it later, since UnstructuredWordDocumentLoader is extremly slow
            loader = UnstructuredWordDocumentLoader(file_path=filepath)
        elif filepath.endswith(".txt"):
            loader = TextLoader(file_path=filepath)

        if loader is None:
            raise RuntimeError("Unsupported type of file")
        
        documents: list[Document] = [] # We can not assign a single value to the document since .pdf are splitted into several files
        try:
            documents = loader.load()
        except Exception:
            raise RuntimeError("File is corrupted")
        
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
            lines: list[str] = document.page_content.split("\n")

            for chunk in text:

                start_l, end_l = self.get_start_end_lines(
                    splitted_text=lines,
                    start_char=chunk.metadata.get("start_index", 0),
                    end_char=chunk.metadata.get("start_index", 0) + len(chunk.page_content)
                )

                self.chunks.append(Chunk(
                    id=len(self.chunks),
                    filename=document.metadata.get("source", ""),
                    page_number=document.metadata.get("page", 0),
                    start_index=chunk.metadata.get("start_index", 0),
                    start_line=start_l,
                    end_line=end_l,
                    text=chunk.page_content
                ))


    '''
    Determines the line, were the chunk starts and ends (1-based indexing)

    Some magic stuff here. To be honest, i understood it after 7th attempt

    splitted_text -> original text splitted by \n
    start_char -> index of symbol, were current chunk starts
    end_char ->  index of symbol, were current chunk ends
    debug_mode -> flag, which enables printing useful info about the process

    TODO: invent more efficient way
    '''
    def get_start_end_lines(self, splitted_text: list[str], start_char: int, end_char: int, debug_mode: bool = False) -> tuple[int, int]:
        if debug_mode:
            logging.info(splitted_text)

        start, end, char_ct = 0, 0, 0
        iter_count = 1

        for i, line in enumerate(splitted_text):
            if debug_mode:
                logging.info(f"start={start_char}, current={char_ct}, end_current={char_ct + len(line) + 1}, end={end_char}, len={len(line)}, iter={iter_count}\n")
            
            if char_ct <= start_char <= char_ct + len(line) + 1:
                start = i + 1
            if char_ct <= end_char <= char_ct + len(line) + 1:
                end = i + 1
                break

            iter_count += 1
            char_ct += len(line) + 1

        if debug_mode:
            logging.info(f"result => {start} {end}\n\n\n")

        return start, end


    def update_nltk(self) -> None:
        nltk.download('punkt')
        nltk.download('averaged_perceptron_tagger')


def main():
    processor = document_processor()
    # processor.update_nltk()
    processor.load_documents([
        "/your_path/samples/sample.txt",
        "/your_path/samples/sample.doc",
        "/your_path/samples/sample.docx",
        "/your_path/samples/sample.pdf"
        ], add_to_unprocessed=True)
    processor.generate_chunks()

    for c in processor.chunks:
        print(c)


if __name__ == "__main__":
    main()
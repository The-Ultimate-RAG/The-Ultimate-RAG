from langchain_community.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from models import Embedder
from chunks import Chunk
import nltk  # used for proper tokenizer workflow
from uuid import \
    uuid4  # for generating unique id as hex (uuid4 is used as it generates ids form pseudo random numbers unlike uuid1 and others)
import numpy as np
from settings import logging, text_splitter_config, embedder_model


# TODO: replace PDFloader since it is completely unusable OR try to fix it


class DocumentProcessor:
    '''
    TODO: determine the most suitable chunk size

    chunks -> the list of chunks from loaded files
    chunks_unsaved -> the list of recently added chunks that have not been saved to db yet
    processed -> the list of files that were already splitted into chunks
    upprocessed -> !processed
    text_splitter -> text splitting strategy
    '''

    def __init__(self):
        self.chunks: list[Chunk] = []
        self.chunks_unsaved: list[Chunk] = []
        self.processed: list[Document] = []
        self.unprocessed: list[Document] = []
        self.embedder = Embedder(embedder_model)
        self.text_splitter = RecursiveCharacterTextSplitter(**text_splitter_config)

    '''
    Measures cosine between two vectors
    '''

    def cosine_similarity(self, vec1, vec2):
        return vec1 @ vec2 / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

    '''
    Updates a list of the most relevant chunks without interacting with db
    '''

    def update_most_relevant_chunk(self, chunk: list[np.float64, Chunk], relevant_chunks: list[list[np.float64, Chunk]],
                                   mx_len=15):
        relevant_chunks.append(chunk)
        for i in range(len(relevant_chunks) - 1, 0, -1):
            if relevant_chunks[i][0] > relevant_chunks[i - 1][0]:
                relevant_chunks[i], relevant_chunks[i - 1] = relevant_chunks[i - 1], relevant_chunks[i]
            else:
                break

        if len(relevant_chunks) > mx_len:
            del relevant_chunks[-1]

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
            loader = PyPDFLoader(
                file_path=filepath)  # splits each presentation into slides and processes it as separate file
        elif filepath.endswith(".docx") or filepath.endswith(".doc"):
            # loader = Docx2txtLoader(file_path=filepath) ## try it later, since UnstructuredWordDocumentLoader is extremly slow
            loader = UnstructuredWordDocumentLoader(file_path=filepath)
        elif filepath.endswith(".txt"):
            loader = TextLoader(file_path=filepath)

        if loader is None:
            raise RuntimeError("Unsupported type of file")

        documents: list[
            Document] = []  # We can not assign a single value to the document since .pdf are splitted into several files
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
        extracted_documents: list[Document] = []

        for doc in documents:
            temp_storage: list[Document] = []

            try:
                temp_storage = self.load_document(filepath=doc,
                                                  add_to_unprocessed=False)  # In some cases it should be True, but i can not imagine any :(
            except Exception as e:
                logging.error("Error at load_documents while loading %s", doc, exc_info=e)
                continue

            for extrc_doc in temp_storage:
                extracted_documents.append(extrc_doc)

                if add_to_unprocessed:
                    self.unprocessed.append(extrc_doc)

        return extracted_documents

    '''
    Generates chunks with recursive splitter from the list of unprocessed files, add files to the list of processed, and clears unprocessed

    TODO: try to split text with other llm (not really needed, but we should at least try it)
    '''

    def generate_chunks(self, query: str = "", embedding: bool = False):
        most_relevant = []

        if embedding:
            query_embedded = self.embedder.encode(query)

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

                newChunk = Chunk(
                    id=uuid4(),
                    filename=document.metadata.get("source", ""),
                    page_number=document.metadata.get("page", 0),
                    start_index=chunk.metadata.get("start_index", 0),
                    start_line=start_l,
                    end_line=end_l,
                    text=chunk.page_content
                )

                if embedding:
                    chunk_embedded = self.embedder.encode(newChunk.text)
                    similarity = self.cosine_similarity(query_embedded, chunk_embedded)
                    self.update_most_relevant_chunk([similarity, newChunk], most_relevant)

                self.chunks.append(newChunk)
                self.chunks_unsaved.append(newChunk)

            self.unprocessed = []
            print(len(self.chunks_unsaved))
        return most_relevant

    '''
    Determines the line, were the chunk starts and ends (1-based indexing)

    Some magic stuff here. To be honest, i understood it after 7th attempt

    TODO: invent more efficient way

    splitted_text -> original text splitted by \n
    start_char -> index of symbol, were current chunk starts
    end_char ->  index of symbol, were current chunk ends
    debug_mode -> flag, which enables printing useful info about the process
    '''

    def get_start_end_lines(self, splitted_text: list[str], start_char: int, end_char: int, debug_mode: bool = False) -> \
    tuple[int, int]:
        if debug_mode:
            logging.info(splitted_text)

        start, end, char_ct = 0, 0, 0
        iter_count = 1

        for i, line in enumerate(splitted_text):
            if debug_mode:
                logging.info(
                    f"start={start_char}, current={char_ct}, end_current={char_ct + len(line) + 1}, end={end_char}, len={len(line)}, iter={iter_count}\n")

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

    '''
    Note: it should be used only once to download tokenizers, futher usage is not recommended
    '''

    def update_nltk(self) -> None:
        nltk.download('punkt')
        nltk.download('averaged_perceptron_tagger')

    '''
    For now the system works as follows: we save recently loaded chunks in two arrays:
        chunks - for all chunks, even for that ones that havn't been saveed to db
        chunks_unsaved - for chunks that have been added recently
    I do not know weather we really need to store all chunks that were added in the 
    current session, but chunks_unsaved are used to avoid dublications while saving to db.
    '''

    def clear_unsaved_chunks(self):
        self.chunks_unsaved = []

    def get_all_chunks(self) -> list[Chunk]:
        return self.chunks

    '''
    If we want to save chunks to db, we need to clear the temp storage to avoid dublications
    '''

    def get_and_save_unsaved_chunks(self) -> list[Chunk]:
        chunks_copy: list[Chunk] = self.chunks.copy()
        self.clear_unsaved_chunks()
        return chunks_copy

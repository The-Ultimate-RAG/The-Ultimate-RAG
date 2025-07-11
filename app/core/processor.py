from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredWordDocumentLoader,
    TextLoader,
    CSVLoader,
    UnstructuredMarkdownLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.core.chunks import Chunk
import nltk  # used for proper tokenizer workflow
from uuid import (
    uuid4,
)  # for generating unique id as hex (uuid4 is used as it generates ids form pseudo random numbers unlike uuid1 and others)
from app.settings import logging, settings
from concurrent.futures import ProcessPoolExecutor
import os
import asyncio
from datetime import datetime



def find_line_sync(splitted_text: list[dict], char) -> int:
    left, right = 0, len(splitted_text) - 1

    while left <= right:
        mid = (left + right) // 2
        line = splitted_text[mid]

        if line["start"] <= char < line["end"]:
            return mid + 1
        elif char < line["start"]:
            right = mid - 1
        else:
            left = mid + 1

    return right

def get_start_end_lines_sync(
    splitted_text: list[dict],
    start_char: int,
    end_char: int,
    debug_mode: bool = False,
) -> tuple[int, int]:
    start = find_line_sync(splitted_text=splitted_text, char=start_char)
    end = find_line_sync(splitted_text=splitted_text, char=end_char)
    return (start, end)

def _chunkinize_sync(document: Document, text: list[str], lines: list[dict]) -> list[Chunk]:
    output: list[Chunk] = []
    for chunk in text:
        start_l, end_l = get_start_end_lines_sync(
            splitted_text=lines,
            start_char=chunk.metadata.get("start_index", 0),
            end_char=chunk.metadata.get("start_index", 0)
            + len(chunk.page_content),
        )

        new_chunk = Chunk(
            id=uuid4(),
            filename=document.metadata.get("source", ""),
            page_number=document.metadata.get("page", 0),
            start_index=chunk.metadata.get("start_index", 0),
            start_line=start_l,
            end_line=end_l,
            text=chunk.page_content,
        )
        # print(new_chunk)
        output.append(new_chunk)
    return output

class DocumentProcessor:
    def __init__(self):
        self.chunks_unsaved: list[Chunk] = []
        self.unprocessed: asyncio.Queue[Document] = asyncio.Queue()
        self.max_workers = min(16, os.cpu_count() or 1)
        self.text_splitter = RecursiveCharacterTextSplitter(
            **settings.text_splitter.model_dump()
        )
        self.chunk_executor = ProcessPoolExecutor(max_workers=self.max_workers)

    async def check_size(self, file_path: str = "") -> bool:
        try:
            size = os.path.getsize(filename=file_path)
        except Exception:
            size = 0

        if size > 1000000:
            return True
        return False

    async def document_multiplexer(self, filepath: str, get_loader: bool = False, get_chunking_strategy: bool = False):
        loader = None
        parallelization = False
        if filepath.endswith(".pdf"):
            loader = PyPDFLoader(
                file_path=filepath
            )  # splits each presentation into slides and processes it as separate file
            parallelization = False
        elif filepath.endswith(".docx") or filepath.endswith(".doc"):
            loader = UnstructuredWordDocumentLoader(file_path=filepath)
        elif filepath.endswith(".txt"):
            loader = TextLoader(file_path=filepath)
        elif filepath.endswith(".csv"):
            loader = CSVLoader(file_path=filepath)
        elif filepath.endswith(".json"):
            loader = TextLoader(file_path=filepath)
        elif filepath.endswith(".md"):
            loader = UnstructuredMarkdownLoader(file_path=filepath)

        if filepath.endswith(".pdf"):
            parallelization = False
        else:
            parallelization = await self.check_size(file_path=filepath)

        if get_loader:
            return loader
        elif get_chunking_strategy:
            return parallelization
        else:
            raise RuntimeError("What to do, my lord?")

    async def load_document(
        self, filepath: str, add_to_unprocessed: bool = False
    ) -> None:
        print(f"Document {os.path.basename(filepath)} is loaded, time - {datetime.now()}")
        loader = await self.document_multiplexer(filepath=filepath, get_loader=True)
        loop = asyncio.get_event_loop()

        if loader is None:
            raise RuntimeError("Unsupported type of file")

        documents: list[Document] = []
        try:
            documents = await loop.run_in_executor(None, loader.load)
            # print("-" * 100, documents, "-" * 100, sep="\n")
        except Exception:
            raise RuntimeError("File is corrupted")

        if add_to_unprocessed:
            for doc in documents:
                await self.unprocessed.put({"document": doc, "path": filepath})

    async def load_documents(self, documents: list[str]) -> None:

        for doc in documents:
            try:
                await self.load_document(filepath=doc, add_to_unprocessed=True)
            except Exception as e:
                logging.error(
                    "Error at load_documents while loading %s", doc, exc_info=e
                )


    async def split_into_groups(self, original_list: list[any], split_by: int = 15) -> list[list[any]]:
        output = []
        for i in range(0, len(original_list), split_by):
            new_group = original_list[i: i + split_by]
            output.append(new_group)
        return output

    async def _chunkinize(self, document: Document, text: list[str], lines: list[dict]) -> list[Chunk]:
        output: list[Chunk] = []
        for chunk in text:
            start_l, end_l = await self.get_start_end_lines(
                splitted_text=lines,
                start_char=chunk.metadata.get("start_index", 0),
                end_char=chunk.metadata.get("start_index", 0)
                + len(chunk.page_content),
            )

            new_chunk = Chunk(
                id=uuid4(),
                filename=document.metadata.get("source", ""),
                page_number=document.metadata.get("page", 0),
                start_index=chunk.metadata.get("start_index", 0),
                start_line=start_l,
                end_line=end_l,
                text=chunk.page_content,
            )
            # print(new_chunk)
            output.append(new_chunk)
        return output

    async def precompute_lines(self, splitted_document: list[str]) -> list[dict]:
        loop = asyncio.get_running_loop()
        def compute_lines():
            current_start = 0
            output: list[dict] = []
            for i, line in enumerate(splitted_document):
                output.append({"id": i + 1, "start": current_start, "end": current_start + len(line) + 1, "text": line})
                current_start += len(line) + 1
            return output
        return await loop.run_in_executor(None, compute_lines)

    async def generate_chunks(self):
        intermediate: list[Chunk] = []
        loop = asyncio.get_event_loop()

        while not self.unprocessed.empty():
            entity = await self.unprocessed.get()
            try:
                document, filepath = entity["document"], entity["path"]
                parallelization = await self.document_multiplexer(filepath=filepath, get_chunking_strategy=True)
                print(f"Strategy --> {"P" if parallelization else "S"}")
                text = await loop.run_in_executor(
                    None, self.text_splitter.split_documents, [document]
                )
                lines: list[dict] = await self.precompute_lines(splitted_document=document.page_content.splitlines())

                if parallelization:
                    print("<------- Apply Parallel Execution ------->")
                    print(f"Document - {os.path.basename(filepath)}")
                    groups = await self.split_into_groups(original_list=text, split_by=50)
                    tasks = [
                        loop.run_in_executor(
                            self.chunk_executor,
                            _chunkinize_sync,
                            document,
                            group,
                            lines
                        )
                        for group in groups
                    ]
                    results = await asyncio.gather(*tasks)
                    for chunks in results:
                        intermediate.extend(chunks)
                    print("<---------------- Done ----------------->")
                else:
                    chunks = await loop.run_in_executor(None, _chunkinize_sync, document, text, lines)
                    intermediate.extend(chunks)
            finally:
                self.unprocessed.task_done()

        self.chunks_unsaved.extend(intermediate)

    async def find_line(self, splitted_text: list[dict], char) -> int:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, find_line_sync, splitted_text, char)

    async def get_start_end_lines(
        self,
        splitted_text: list[dict],
        start_char: int,
        end_char: int,
        debug_mode: bool = False,
    ) -> tuple[int, int]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, get_start_end_lines_sync, splitted_text, start_char, end_char, debug_mode)

    async def update_nltk(self) -> None:
        nltk.download("punkt")
        nltk.download("averaged_perceptron_tagger")

    async def get_and_save_unsaved_chunks(self) -> list[Chunk]:
        chunks_copy: list[Chunk] = self.chunks_unsaved.copy()
        await self.clear_unsaved_chunks()
        return chunks_copy

    async def clear_unsaved_chunks(self):
        self.chunks_unsaved = []

    async def get_all_chunks(self) -> list[Chunk]:
        return self.chunks_unsaved


# async def main():
#     print(f"Start time - {datetime.now()}")
#     proc = DocumentProcessor()
#     base = "/home/danil/Downloads/Tests/test"
#     docs = []
#     for i in range(8):
#         docs.append(base + str(i) + ".txt")
#     await proc.load_documents(docs)
#     await proc.generate_chunks()
#     chunks = await proc.get_and_save_unsaved_chunks()
#     print(len(chunks))
#     print(f"End time - {datetime.now()}")
# asyncio.run(main())
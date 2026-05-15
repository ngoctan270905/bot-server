import os
from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_core.documents import Document

class DocumentProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 100):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """Cắt nhỏ các documents."""
        return self.text_splitter.split_documents(documents)

    @staticmethod
    async def load_file(file_path: str) -> List[Document]:
        """Load nội dung từ file (PDF, Docx, TXT)."""
        if not os.path.exists(file_path):
            return []
            
        ext = os.path.splitext(file_path)[1].lower()
        try:
            if ext == ".pdf":
                loader = PyPDFLoader(file_path)
                return loader.load()
            elif ext == ".docx":
                loader = Docx2txtLoader(file_path)
                return loader.load()
            elif ext == ".txt":
                loader = TextLoader(file_path, encoding="utf-8")
                return loader.load()
            else:
                return []
        except Exception as e:
            from loguru import logger
            logger.error(f"Error loading file {file_path}: {e}")
            return []

document_processor = DocumentProcessor()

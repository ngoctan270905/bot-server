import os
from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
from langchain_core.documents import Document

class DocumentProcessor:
  """
  Xử lý tài liệu đầu vào phục vụ cho các tác vụ AI/RAG.

  Class này hỗ trợ:
  - Đọc nội dung từ các định dạng file phổ biến như PDF, DOCX, TXT
  - Chuyển đổi nội dung thành danh sách Document của LangChain
  - Chia nhỏ nội dung thành các chunk để phục vụ embedding hoặc tìm kiếm ngữ nghĩa

  Attributes:
      text_splitter (RecursiveCharacterTextSplitter):
          Bộ chia văn bản thành nhiều đoạn nhỏ.
  """

  def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
    """
    Khởi tạo DocumentProcessor với cấu hình chunking.

    Args:
        chunk_size (int):
            Số ký tự tối đa trong mỗi chunk.

        chunk_overlap (int):
            Số ký tự chồng lấp giữa các chunk
            nhằm giữ ngữ cảnh liên tục.
    """
    self.text_splitter = RecursiveCharacterTextSplitter(
      chunk_size=chunk_size,
      chunk_overlap=chunk_overlap,
      length_function=len,
    )

  def chunk_documents(self, documents: List[Document]) -> List[Document]:
    """
    Chia nhỏ danh sách tài liệu thành nhiều chunk nhỏ hơn.

    Args:
        documents (List[Document]):
            Danh sách tài liệu cần xử lý.

    Returns:
        List[Document]:
            Danh sách document sau khi được chia chunk.
    """
    return self.text_splitter.split_documents(documents)

  @staticmethod
  async def load_file(file_path: str) -> List[Document]:
    """
    Đọc nội dung từ file và chuyển thành danh sách Document.

    Hỗ trợ các định dạng:
    - PDF (.pdf)
    - Word (.docx)
    - Text (.txt)

    Args:
        file_path (str):
            Đường dẫn tới file cần đọc.

    Returns:
        List[Document]:
            Danh sách document được load từ file.
            Trả về danh sách rỗng nếu file không tồn tại,
            không hỗ trợ định dạng hoặc xảy ra lỗi.
    """
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

  @staticmethod
  async def count_characters(file_path: str) -> int:
    """
    Đếm tổng số ký tự trong file (PDF, Word, Text).
    """
    docs = await DocumentProcessor.load_file(file_path)
    if not docs:
      return 0
    return sum(len(doc.page_content) for doc in docs)

document_processor = DocumentProcessor()

"""文档解析器 - 支持多种格式"""
import os
from typing import List
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document as DocxDocument
except ImportError:
    DocxDocument = None


class DocumentParser:
    """将文档解析为文本块"""

    @staticmethod
    def parse_pdf(file_path: str) -> str:
        """解析 PDF 文件为文本"""
        if PdfReader is None:
            raise ImportError("未安装 pypdf。运行: pip install pypdf")

        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()

    @staticmethod
    def parse_docx(file_path: str) -> str:
        """解析 DOCX 文件为文本"""
        if DocxDocument is None:
            raise ImportError("未安装 python-docx。运行: pip install python-docx")

        doc = DocxDocument(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text.strip()

    @staticmethod
    def parse_txt(file_path: str) -> str:
        """解析 TXT 文件为文本"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()

    @staticmethod
    def parse_md(file_path: str) -> str:
        """解析 Markdown 文件为文本"""
        return DocumentParser.parse_txt(file_path)

    @classmethod
    def parse(cls, file_path: str) -> str:
        """自动检测格式并解析"""
        ext = Path(file_path).suffix.lower()

        if ext == '.pdf':
            return cls.parse_pdf(file_path)
        elif ext in ['.doc', '.docx']:
            return cls.parse_docx(file_path)
        elif ext == '.txt':
            return cls.parse_txt(file_path)
        elif ext == '.md':
            return cls.parse_md(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {ext}")

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """将文本分割为重叠的块"""
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]

            # 尝试在句子边界处断开
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)

                if break_point > chunk_size * 0.5:  # 至少保留 50% 的块
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1

            chunks.append(chunk.strip())
            start = end - overlap

        return chunks

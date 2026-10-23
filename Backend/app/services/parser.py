import os
import pandas as pd
from docx import Document
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

class DocumentParser:
    @staticmethod
    def parse_file(file_path: str, file_extension: str) -> str:
        """Extracts text from PDF, DOCX, XLSX, or TXT files."""
        text = ""
        ext = file_extension.lower()

        if ext == ".pdf":
            reader = PdfReader(file_path)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"

        elif ext in [".docx", ".doc"]:
            doc = Document(file_path)
            for para in doc.paragraphs:
                if para.text.strip():
                    text += para.text + "\n"

        elif ext in [".xlsx", ".xls", ".csv"]:
            if ext == ".csv":
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            # Convert tabular dataframe to clean markdown or text representation
            text = df.to_markdown(index=False)

        elif ext == ".txt":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

        else:
            raise ValueError(f"Unsupported file format: {ext}")

        return text

    @staticmethod
    def get_text_chunks(text: str, chunk_size: int = 1000, chunk_overlap: int = 200):
        """Splits large text into smaller chunks for vector embedding."""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )
        return splitter.split_text(text)
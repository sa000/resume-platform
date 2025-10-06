import logging
import docx
from pypdf import PdfReader

logger = logging.getLogger(__name__)

def extract_text_from_docx(file_path: str) -> str:
    """Extract text content from a DOCX file including tables."""
    doc = docx.Document(file_path)
    text_chunks = []

    # paragraphs
    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            text_chunks.append(paragraph.text)

    # tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                cell_text = cell.text.strip()
                if cell_text:
                    text_chunks.append(cell_text)

    text = "\n".join(text_chunks)
    print(f"Extracted {len(text)} characters from DOCX (with tables)")
    return text


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text content from a PDF file."""
    logger.info(f"Reading PDF: {file_path}")
    reader = PdfReader(file_path)
    text = "\n".join([page.extract_text() for page in reader.pages])
    logger.info(f"Extracted {len(text)} characters from PDF")
    return text


def extract_text(file_path: str) -> str:
    """Extract text from a resume file based on file extension."""
    if file_path.endswith(".docx"):
        return extract_text_from_docx(file_path)
    elif file_path.endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path}")
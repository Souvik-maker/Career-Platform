from pypdf import PdfReader
import io

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    "Extracts unstructured raw text from uploaded PDF bytes."
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text
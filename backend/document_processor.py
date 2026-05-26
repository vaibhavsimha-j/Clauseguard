import hashlib
import io


class DocumentProcessor:
    def process(self, uploaded_file) -> tuple[str, list[str], str]:
        data = uploaded_file.read()
        contract_id = hashlib.md5(data).hexdigest()[:12]

        name = uploaded_file.name.lower()
        if name.endswith(".pdf"):
            text = self._parse_pdf(data)
        elif name.endswith(".docx"):
            text = self._parse_docx(data)
        else:
            text = data.decode("utf-8", errors="replace")

        chunks = self._chunk(text)
        return contract_id, chunks, text

    def _parse_pdf(self, data: bytes) -> str:
        import fitz

        doc = fitz.open(stream=data, filetype="pdf")
        pages = [page.get_text() for page in doc]
        doc.close()
        return "\n\n".join(pages)

    def _parse_docx(self, data: bytes) -> str:
        from docx import Document

        doc = Document(io.BytesIO(data))
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())

    def _chunk(self, text: str, size: int = 900, overlap: int = 150) -> list[str]:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks: list[str] = []
        current = ""

        for para in paragraphs:
            if len(current) + len(para) > size and current:
                chunks.append(current.strip())
                current = current[-overlap:] + "\n\n" + para
            else:
                current = (current + "\n\n" + para).strip() if current else para

        if current.strip():
            chunks.append(current.strip())

        return chunks or [text[:2000]]

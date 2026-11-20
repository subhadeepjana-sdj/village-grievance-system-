import os
import re
import uuid
import logging
from typing import List, Dict, Any
from app.services.embedding_service import embedding_service
from app.services.qdrant_service import qdrant_service

logger = logging.getLogger("uvicorn.error")

class DocumentParserService:
    def extract_text_from_file(self, file_path: str, ext: str) -> List[Dict[str, Any]]:
        """Extracts text page-by-page or section-by-section."""
        pages = []
        ext = ext.lower()

        if ext == ".pdf":
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(file_path)
                for i, page in enumerate(doc):
                    text = page.get_text("text").strip()
                    if text:
                        pages.append({"page_number": i + 1, "text": text})
            except Exception as e:
                logger.warning(f"PyMuPDF failed ({e}), using basic text fallback.")
                pages = self._read_plain_text(file_path)

        elif ext in [".docx", ".doc"]:
            try:
                import docx
                doc = docx.Document(file_path)
                full_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
                pages.append({"page_number": 1, "text": full_text})
            except Exception as e:
                logger.warning(f"python-docx failed ({e}), using basic text fallback.")
                pages = self._read_plain_text(file_path)

        else:
            pages = self._read_plain_text(file_path)

        return pages

    def _read_plain_text(self, file_path: str) -> List[Dict[str, Any]]:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read().strip()
                return [{"page_number": 1, "text": content}] if content else []
        except Exception as e:
            logger.error(f"Error reading plain text file {file_path}: {e}")
            return []

    def clean_and_chunk(
        self, 
        pages: List[Dict[str, Any]], 
        chunk_size_words: int = 250, 
        overlap_words: int = 40
    ) -> List[Dict[str, Any]]:
        chunks = []
        
        for p in pages:
            text = p["text"]
            # Clean text
            text = re.sub(r'\s+', ' ', text)
            words = text.split()
            
            if not words:
                continue

            start = 0
            while start < len(words):
                end = min(start + chunk_size_words, len(words))
                chunk_words = words[start:end]
                chunk_text = " ".join(chunk_words)
                
                chunks.append({
                    "page_number": p["page_number"],
                    "text": chunk_text
                })
                
                if end == len(words):
                    break
                start += (chunk_size_words - overlap_words)

        return chunks

    def process_and_index_document(
        self, 
        file_path: str, 
        document_id: int, 
        title: str, 
        department: str = "", 
        village: str = "", 
        source: str = "", 
        category: str = "", 
        version: str = "1.0",
        effective_date: str = ""
    ) -> int:
        ext = os.path.splitext(file_path)[1]
        pages = self.extract_text_from_file(file_path, ext)
        chunks = self.clean_and_chunk(pages)

        if not chunks:
            logger.warning(f"No text extracted for document ID {document_id}")
            return 0

        points = []
        texts_to_embed = [c["text"] for c in chunks]
        embeddings = embedding_service.generate_embeddings(texts_to_embed)

        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            # Numeric point ID generated deterministically from document_id + chunk index
            point_id = (document_id * 10000) + (i + 1)
            
            points.append({
                "id": point_id,
                "vector": emb,
                "payload": {
                    "document_id": document_id,
                    "title": title,
                    "chunk_id": f"doc_{document_id}_chunk_{i+1}",
                    "source": source or title,
                    "department": department,
                    "village": village,
                    "category": category,
                    "document_version": version,
                    "date": effective_date,
                    "page_number": chunk["page_number"],
                    "text": chunk["text"]
                }
            })

        qdrant_service.upsert_chunks(points)
        return len(points)

document_parser_service = DocumentParserService()

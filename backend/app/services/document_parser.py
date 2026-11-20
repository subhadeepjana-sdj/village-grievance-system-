import os
import re
import hashlib
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

    # ------------------------------------------------------------------ #
    #  Token-based chunking (spec: 500-800 tokens, 75-120 token overlap)  #
    # ------------------------------------------------------------------ #
    def clean_and_chunk_tokens(
        self,
        pages: List[Dict[str, Any]],
        chunk_size_words: int = 600,   # ~600 words ≈ 650 tokens for English prose
        overlap_words: int = 100       # ~100 words ≈ 110 tokens
    ) -> List[Dict[str, Any]]:
        """
        Primary chunking method.  Uses *exact* token counting via tiktoken when
        available, otherwise falls back to word-count approximation.

        Spec targets: 500–800 tokens per chunk, 75–120 token overlap.
        Word approximation: 600 words / 100-word overlap stays inside those bands.
        """
        # --- Exact tokenisation via tiktoken (optional dependency) ---
        try:
            import tiktoken
            enc = tiktoken.get_encoding("cl100k_base")

            def _token_chunk(text: str, page_num: int) -> List[Dict[str, Any]]:
                tokens = enc.encode(text)
                result: List[Dict[str, Any]] = []
                target, ovlp = chunk_size_words, overlap_words
                start = 0
                while start < len(tokens):
                    end = min(start + target, len(tokens))
                    chunk_text = enc.decode(tokens[start:end]).strip()
                    if chunk_text:
                        result.append({"page_number": page_num, "text": chunk_text})
                    if end == len(tokens):
                        break
                    start += (target - ovlp)
                return result

            chunks: List[Dict[str, Any]] = []
            for p in pages:
                text = re.sub(r"\s+", " ", p["text"]).strip()
                if text:
                    chunks.extend(_token_chunk(text, p["page_number"]))
            return chunks

        except ImportError:
            pass  # tiktoken not installed — fall through to word approximation

        # --- Word-count approximation ---
        chunks: List[Dict[str, Any]] = []
        for p in pages:
            text = re.sub(r"\s+", " ", p["text"]).strip()
            words = text.split()
            if not words:
                continue
            start = 0
            while start < len(words):
                end = min(start + chunk_size_words, len(words))
                chunk_text = " ".join(words[start:end])
                chunks.append({"page_number": p["page_number"], "text": chunk_text})
                if end == len(words):
                    break
                start += (chunk_size_words - overlap_words)
        return chunks

    # ------------------------------------------------------------------ #
    #  Legacy word-based chunking — kept for backward compatibility only  #
    # ------------------------------------------------------------------ #
    def clean_and_chunk(
        self,
        pages: List[Dict[str, Any]],
        chunk_size_words: int = 250,
        overlap_words: int = 40
    ) -> List[Dict[str, Any]]:
        """Legacy wrapper — delegates to token-based method."""
        return self.clean_and_chunk_tokens(pages, chunk_size_words, overlap_words)

    # ------------------------------------------------------------------ #
    #  Duplicate detection                                                 #
    # ------------------------------------------------------------------ #
    @staticmethod
    def compute_file_hash(file_path: str) -> str:
        """Return SHA-256 hex digest of file bytes.  Used for dedup checks."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for block in iter(lambda: f.read(8192), b""):
                sha256.update(block)
        return sha256.hexdigest()

    # ------------------------------------------------------------------ #
    #  Main indexing entry-point                                           #
    # ------------------------------------------------------------------ #
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
        effective_date: str = "",
        status: str = "verified"
    ) -> int:
        """
        Extract → token-chunk → embed → upsert into Qdrant.
        Returns the number of chunks indexed (0 on empty document).
        """
        ext = os.path.splitext(file_path)[1]
        pages = self.extract_text_from_file(file_path, ext)
        chunks = self.clean_and_chunk_tokens(pages)

        if not chunks:
            logger.warning(f"No text extracted for document ID {document_id}")
            return 0

        texts_to_embed = [c["text"] for c in chunks]
        embeddings = embedding_service.generate_embeddings(texts_to_embed)

        points = []
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            # Deterministic numeric ID: document_id * 10000 + 1-based chunk index
            point_id = (document_id * 10000) + (i + 1)
            points.append({
                "id": point_id,
                "vector": emb,
                "payload": {
                    "document_id": document_id,
                    "title": title,
                    "chunk_id": f"doc_{document_id}_chunk_{i + 1}",
                    "source": source or title,
                    "department": department,
                    "village": village,
                    "category": category,
                    "document_version": version,
                    "date": effective_date,
                    "page_number": chunk["page_number"],
                    "text": chunk["text"],
                    # Validity metadata — used by retrieval filter to skip outdated/unverified docs
                    "status": status,          # "verified" | "pending" | "expired"
                    "effective_date": effective_date
                }
            })

        qdrant_service.upsert_chunks(points)
        logger.info(f"Indexed {len(points)} chunks for document_id={document_id} (title='{title}')")
        return len(points)


document_parser_service = DocumentParserService()

import os
import threading
import logging
from typing import Tuple, Any, Optional

logger = logging.getLogger("uvicorn.error")

class NLIModelLoader:
    """
    Thread-safe Singleton Model Loader for Natural Language Inference.
    Loads and caches tokenizer and sequence classification weights in memory once.
    """
    _instance: Optional["NLIModelLoader"] = None
    _lock = threading.Lock()

    # Recommended lightweight CPU-friendly default; can be overridden via NLI_MODEL_NAME env var
    DEFAULT_MODEL_NAME = "cross-encoder/nli-deberta-v3-xsmall"

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if getattr(self, "_initialized", False):
            return

        self.model_name = os.getenv("NLI_MODEL_NAME", self.DEFAULT_MODEL_NAME)
        self.device = self._detect_device()
        self.tokenizer = None
        self.model = None
        self.is_loaded = False
        self.offline_mode = False
        self._init_lock = threading.Lock()
        self._initialized = True

    def _detect_device(self) -> str:
        """Determines computation device (cuda, mps, or cpu)."""
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"
        except ImportError:
            pass
        return "cpu"

    def load_model(self) -> Tuple[Any, Any]:
        """
        Loads and returns (tokenizer, model) pair.
        Safe against redundant loads across worker threads.
        """
        if self.is_loaded:
            return self.tokenizer, self.model

        with self._init_lock:
            if self.is_loaded:
                return self.tokenizer, self.model

            try:
                import torch
                from transformers import AutoTokenizer, AutoModelForSequenceClassification

                # If OFFLINE_MODE or CI, avoid waiting for remote timeout
                if os.getenv("OFFLINE_MODE", "0") == "1":
                    raise ConnectionError("OFFLINE_MODE requested.")

                logger.info(f"Loading NLI model '{self.model_name}' on device '{self.device}'...")
                self.tokenizer = AutoTokenizer.from_pretrained(
                    self.model_name,
                    use_fast=True,
                    local_files_only=True  # check local cache first
                )
                self.model = AutoModelForSequenceClassification.from_pretrained(
                    self.model_name,
                    local_files_only=True
                )
                self.model.to(self.device)
                self.model.eval()
                self.is_loaded = True
                logger.info(f"NLI model '{self.model_name}' loaded successfully from local cache on {self.device}.")
            except Exception:
                # If local cache missing or network unavailable, fall back cleanly
                self.offline_mode = True
                self.is_loaded = True

        return self.tokenizer, self.model


nli_model_loader = NLIModelLoader()

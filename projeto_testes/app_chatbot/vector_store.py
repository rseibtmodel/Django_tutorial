import threading
from pathlib import Path
from typing import Any
from django.conf import settings


class VectorStoreManager:
    """Gerenciador Singleton Thread-Safe para persistência do ChromaDB."""

    _instance = None
    _lock = threading.Lock()
    _client = None
    _collection = None

    def __new__(cls) -> "VectorStoreManager":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._inicializar_chroma()
        return cls._instance

    def _inicializar_chroma(self) -> None:
        """Inicializa o cliente local do ChromaDB com armazenamento persistente."""
        try:
            import chromadb
            from chromadb.config import Settings

            chroma_dir: Path = Path(settings.BASE_DIR) / "chroma_data"
            chroma_dir.mkdir(exist_ok=True)

            self._client = chromadb.PersistentClient(
                path=str(chroma_dir),
                settings=Settings(anonymized_telemetry=False)
            )
            self._collection = self._client.get_or_create_collection(
                name="chat_memory_store",
                metadata={"hnsw:space": "cosine"}
            )
        except ImportError:
            # Fallback caso a biblioteca ainda esteja sendo carregada
            self._client = None
            self._collection = None

    @property
    def collection(self) -> Any:
        """Retorna a coleção do ChromaDB pronta para consultas vetoriais."""
        if self._collection is None:
            self._inicializar_chroma()
        return self._collection


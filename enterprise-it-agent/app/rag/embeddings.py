from functools import lru_cache
from typing import Any

from langchain_core.embeddings import Embeddings

from app.core.config import settings


class BGEM3Embeddings(Embeddings):
    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        device: str = "cuda",
        use_fp16: bool = True,
        batch_size: int = 8,
    ) -> None:
        try:
            from FlagEmbedding import BGEM3FlagModel
        except ImportError as exc:
            raise RuntimeError(
                "FlagEmbedding is not installed. Run `pip install FlagEmbedding torch` "
                "inside the virtual environment."
            ) from exc

        self.model_name = model_name
        self.device = device
        self.use_fp16 = use_fp16
        self.batch_size = batch_size
        self._model = BGEM3FlagModel(
            model_name,
            use_fp16=use_fp16,
            device=device,
        )

    def _encode(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        payload: list[list[float]] = []
        for index in range(0, len(texts), self.batch_size):
            batch = texts[index : index + self.batch_size]
            result: dict[str, Any] = self._model.encode(
                batch,
                batch_size=len(batch),
                max_length=8192,
            )
            dense_vecs = result["dense_vecs"]
            payload.extend(dense_vecs.tolist())
        return payload

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._encode(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._encode([text])[0]


@lru_cache(maxsize=1)
def build_embeddings() -> BGEM3Embeddings:
    return BGEM3Embeddings(
        model_name=settings.embedding_model_name,
        device=settings.embedding_device,
        use_fp16=settings.embedding_use_fp16,
        batch_size=settings.embedding_batch_size,
    )

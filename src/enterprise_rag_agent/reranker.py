from __future__ import annotations

from typing import Any


class BGEReranker:
    def __init__(
        self,
        model_name: str = "BAAI/bge-reranker-v2-m3",
        device: str = "cuda",
        use_fp16: bool = True,
        batch_size: int = 8,
    ) -> None:
        try:
            from FlagEmbedding import FlagAutoReranker
        except ImportError as exc:
            raise RuntimeError(
                "FlagEmbedding is not installed. Run `pip install FlagEmbedding torch` "
                "inside the project's virtual environment."
            ) from exc

        self.model_name = model_name
        self.device = device
        self.use_fp16 = use_fp16
        self.batch_size = batch_size
        self._model = FlagAutoReranker.from_finetuned(
            model_name_or_path=model_name,
            use_fp16=use_fp16,
            devices=device,
            batch_size=batch_size,
        )

    def rerank(
        self,
        query: str,
        docs: list[dict[str, Any]],
        top_k: int,
    ) -> list[dict[str, Any]]:
        if not docs:
            return docs

        scored_docs: list[dict[str, Any]] = []
        for index in range(0, len(docs), self.batch_size):
            batch = docs[index : index + self.batch_size]
            pairs = [[query, doc["content"]] for doc in batch]
            scores = self._model.compute_score(pairs)
            if not isinstance(scores, list):
                scores = [scores]
            for doc, score in zip(batch, scores):
                enriched = dict(doc)
                enriched["rerank_score"] = float(score)
                scored_docs.append(enriched)

        scored_docs.sort(key=lambda item: item["rerank_score"], reverse=True)
        return scored_docs[:top_k]

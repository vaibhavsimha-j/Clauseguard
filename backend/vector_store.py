"""
Pinecone-backed vector store — direct Pinecone client (no langchain-pinecone).

Embeddings: BAAI/bge-small-en-v1.5 (sentence-transformers).
Groq has no embeddings API, so we use the best open-weights model
from the Llama/HuggingFace ecosystem — 384-dim, ~130 MB, CPU-friendly.
"""

from langchain_huggingface import HuggingFaceEmbeddings
from pinecone import Pinecone, ServerlessSpec

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM = 384


class VectorStore:
    def __init__(self, pinecone_api_key: str, index_name: str = "clauseguard") -> None:
        self._embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

        pc = Pinecone(api_key=pinecone_api_key)

        try:
            pc.describe_index(index_name)
        except Exception:
            pc.create_index(
                name=index_name,
                dimension=EMBEDDING_DIM,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )

        self._index = pc.Index(index_name)

    def add_document(self, contract_id: str, chunks: list[str], filename: str = "") -> None:
        embeddings = self._embeddings.embed_documents(chunks)
        vectors = [
            {
                "id": f"{contract_id}_{i}",
                "values": emb,
                "metadata": {"contract_id": contract_id, "text": chunk, "source": filename},
            }
            for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
        ]
        for i in range(0, len(vectors), 100):
            self._index.upsert(vectors=vectors[i:i + 100])

    def search(self, query: str, contract_id: str, k: int = 5) -> list[str]:
        query_embedding = self._embeddings.embed_query(query)
        results = self._index.query(
            vector=query_embedding,
            top_k=k,
            filter={"contract_id": {"$eq": contract_id}},
            include_metadata=True,
        )
        return [
            m.metadata["text"]
            for m in results.matches
            if m.metadata and "text" in m.metadata
        ]

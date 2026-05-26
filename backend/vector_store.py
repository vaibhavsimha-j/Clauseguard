"""
Pinecone-backed vector store via LangChain.

Embeddings: BAAI/bge-small-en-v1.5 (sentence-transformers).
Groq has no embeddings API, so we use the best open-weights model
from the Llama/HuggingFace ecosystem — 384-dim, ~130 MB, CPU-friendly.
"""

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import Pinecone as LangchainPinecone
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

        api_key = pinecone_api_key

        pc = Pinecone(api_key=api_key)

        # Create serverless index on first run if it doesn't exist
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
        # LangChain wrapper: handles upsert and similarity search
        self._store = LangchainPinecone(index=self._index, embedding=self._embeddings)

    def add_document(self, contract_id: str, chunks: list[str], filename: str = "") -> None:
        metadatas = [{"contract_id": contract_id, "source": filename} for _ in chunks]
        self._store.add_texts(texts=chunks, metadatas=metadatas)

    def search(self, query: str, contract_id: str, k: int = 5) -> list[str]:
        docs = self._store.similarity_search(
            query,
            k=k,
            filter={"contract_id": {"$eq": contract_id}},
        )
        return [doc.page_content for doc in docs]

    def as_retriever(self, contract_id: str, k: int = 5):
        return self._store.as_retriever(
            search_kwargs={"k": k, "filter": {"contract_id": {"$eq": contract_id}}},
        )

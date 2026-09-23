"""
RAG Pipeline Implementation for Enterprise LLM Platform
Supports two-stage retrieval: vector search → reranking → LLM generation
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
import openai  # Compatible with vLLM OpenAI API

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Document:
    """Document with metadata"""
    id: str
    text: str
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None
    score: Optional[float] = None


@dataclass
class RAGConfig:
    """RAG pipeline configuration"""
    # Embedding model
    embedding_model: str = "BAAI/bge-large-en-v1.5"  # 1024 dimensions
    embedding_batch_size: int = 32

    # Vector database
    vector_db_host: str = "qdrant"
    vector_db_port: int = 6333
    collection_name: str = "enterprise_knowledge"

    # Retrieval parameters
    retrieval_top_k: int = 100  # Initial retrieval
    rerank_top_k: int = 10      # After reranking
    min_relevance_score: float = 0.7

    # LLM parameters
    llm_endpoint: str = "http://vllm-llama-3-70b/v1"
    llm_model: str = "llama-3-70b"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2048
    llm_top_p: float = 0.95

    # Context window
    max_context_tokens: int = 3000  # Reserve tokens for context

    # Reranking
    rerank_model: str = "BAAI/bge-reranker-large"
    enable_reranking: bool = True

    # Safety
    enable_guardrails: bool = True
    pii_detection: bool = True


class RAGPipeline:
    """
    Two-stage RAG pipeline:
    1. Dense retrieval: semantic search using vector embeddings
    2. Reranking: cross-encoder to rerank top candidates
    3. Generation: LLM with retrieved context
    """

    def __init__(self, config: RAGConfig):
        self.config = config

        # Initialize embedding model
        logger.info(f"Loading embedding model: {config.embedding_model}")
        self.embedding_model = SentenceTransformer(config.embedding_model)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()

        # Initialize reranking model
        if config.enable_reranking:
            logger.info(f"Loading reranking model: {config.rerank_model}")
            self.rerank_model = SentenceTransformer(config.rerank_model)

        # Initialize vector database client
        self.vector_db = QdrantClient(
            host=config.vector_db_host,
            port=config.vector_db_port,
            timeout=30.0
        )

        # Initialize collection if not exists
        self._init_collection()

        # Initialize LLM client (OpenAI-compatible API)
        openai.api_base = config.llm_endpoint
        openai.api_key = "EMPTY"  # vLLM doesn't require key
        self.llm_client = openai

        logger.info("RAG pipeline initialized successfully")

    def _init_collection(self):
        """Initialize Qdrant collection for vector storage"""
        collections = self.vector_db.get_collections().collections
        collection_names = [col.name for col in collections]

        if self.config.collection_name not in collection_names:
            logger.info(f"Creating collection: {self.config.collection_name}")
            self.vector_db.create_collection(
                collection_name=self.config.collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE
                )
            )
            logger.info("Collection created successfully")

    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for text"""
        embedding = self.embedding_model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True  # Normalize for cosine similarity
        )
        return embedding

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for batch of texts"""
        embeddings = self.embedding_model.encode(
            texts,
            batch_size=self.config.embedding_batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 100
        )
        return embeddings

    async def add_documents(
        self,
        documents: List[Document],
        batch_size: int = 100
    ) -> int:
        """Add documents to vector database"""
        logger.info(f"Adding {len(documents)} documents to vector database")

        # Generate embeddings
        texts = [doc.text for doc in documents]
        embeddings = self.embed_batch(texts)

        # Prepare points for Qdrant
        points = []
        for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
            point = PointStruct(
                id=doc.id,
                vector=embedding.tolist(),
                payload={
                    "text": doc.text,
                    "metadata": doc.metadata,
                    "indexed_at": datetime.utcnow().isoformat()
                }
            )
            points.append(point)

        # Batch upsert
        total_uploaded = 0
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            self.vector_db.upsert(
                collection_name=self.config.collection_name,
                points=batch
            )
            total_uploaded += len(batch)
            logger.info(f"Uploaded {total_uploaded}/{len(points)} documents")

        return total_uploaded

    async def retrieve_dense(
        self,
        query: str,
        top_k: int = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Stage 1: Dense retrieval using vector similarity
        Returns top-k most similar documents
        """
        if top_k is None:
            top_k = self.config.retrieval_top_k

        # Generate query embedding
        query_embedding = self.embed_text(query)

        # Build filter if provided
        query_filter = None
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(
                    FieldCondition(
                        key=f"metadata.{key}",
                        match=MatchValue(value=value)
                    )
                )
            query_filter = Filter(must=conditions)

        # Search vector database
        results = self.vector_db.search(
            collection_name=self.config.collection_name,
            query_vector=query_embedding.tolist(),
            limit=top_k,
            query_filter=query_filter,
            score_threshold=self.config.min_relevance_score
        )

        # Convert to Document objects
        documents = []
        for result in results:
            doc = Document(
                id=result.id,
                text=result.payload["text"],
                metadata=result.payload["metadata"],
                score=result.score
            )
            documents.append(doc)

        logger.info(f"Dense retrieval found {len(documents)} documents (query: {query[:50]}...)")
        return documents

    async def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: int = None
    ) -> List[Document]:
        """
        Stage 2: Rerank documents using cross-encoder
        More accurate but slower than vector search
        """
        if not self.config.enable_reranking:
            return documents[:top_k or self.config.rerank_top_k]

        if top_k is None:
            top_k = self.config.rerank_top_k

        # Prepare query-document pairs
        pairs = [[query, doc.text] for doc in documents]

        # Compute reranking scores
        rerank_scores = self.rerank_model.encode(
            pairs,
            convert_to_numpy=True,
            show_progress_bar=False
        )

        # Update document scores
        for doc, score in zip(documents, rerank_scores):
            doc.score = float(score)

        # Sort by rerank score
        documents.sort(key=lambda x: x.score, reverse=True)

        logger.info(f"Reranking selected top {top_k} documents")
        return documents[:top_k]

    def _build_context(
        self,
        documents: List[Document],
        max_tokens: int = None
    ) -> str:
        """Build context string from documents, respecting token limit"""
        if max_tokens is None:
            max_tokens = self.config.max_context_tokens

        context_parts = []
        total_tokens = 0

        for i, doc in enumerate(documents):
            # Estimate tokens (rough: 1 token ≈ 4 characters)
            doc_tokens = len(doc.text) // 4

            if total_tokens + doc_tokens > max_tokens:
                logger.info(f"Context limit reached, using {i} of {len(documents)} documents")
                break

            # Format document with metadata
            source = doc.metadata.get("source", "Unknown")
            timestamp = doc.metadata.get("timestamp", "N/A")

            context_parts.append(
                f"[Document {i+1}] (Source: {source}, Date: {timestamp})\n"
                f"{doc.text}\n"
            )
            total_tokens += doc_tokens

        context = "\n".join(context_parts)
        logger.info(f"Built context with {len(context_parts)} documents (~{total_tokens} tokens)")
        return context

    async def generate(
        self,
        query: str,
        context: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Stage 3: Generate response using LLM with retrieved context
        """
        if system_prompt is None:
            system_prompt = (
                "You are a helpful AI assistant. Answer the question based on the provided context. "
                "If the context doesn't contain enough information, say so. "
                "Always cite the document numbers when referencing information."
            )

        # Build prompt
        prompt = f"""Context:
{context}

Question: {query}

Answer:"""

        # Call LLM
        logger.info(f"Generating response with {self.config.llm_model}")
        try:
            response = await asyncio.to_thread(
                self.llm_client.ChatCompletion.create,
                model=self.config.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.llm_temperature,
                max_tokens=self.config.llm_max_tokens,
                top_p=self.config.llm_top_p,
                stream=False
            )

            answer = response.choices[0].message.content
            usage = response.usage

            logger.info(f"Generation complete (tokens: {usage.total_tokens})")

            return {
                "answer": answer,
                "model": self.config.llm_model,
                "usage": {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens
                }
            }
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise

    async def query(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        return_sources: bool = True
    ) -> Dict[str, Any]:
        """
        End-to-end RAG query:
        1. Retrieve relevant documents
        2. Rerank for relevance
        3. Generate answer with LLM
        """
        start_time = datetime.utcnow()

        # Stage 1: Dense retrieval
        documents = await self.retrieve_dense(query, filters=filters)

        if not documents:
            return {
                "answer": "I couldn't find any relevant information in the knowledge base.",
                "sources": [],
                "latency_ms": (datetime.utcnow() - start_time).total_seconds() * 1000
            }

        # Stage 2: Reranking
        documents = await self.rerank(query, documents)

        # Build context from top documents
        context = self._build_context(documents)

        # Stage 3: Generate answer
        generation_result = await self.generate(query, context)

        # Build response
        end_time = datetime.utcnow()
        latency_ms = (end_time - start_time).total_seconds() * 1000

        response = {
            "answer": generation_result["answer"],
            "model": generation_result["model"],
            "usage": generation_result["usage"],
            "latency_ms": latency_ms,
            "num_documents_retrieved": len(documents),
        }

        if return_sources:
            response["sources"] = [
                {
                    "text": doc.text[:200] + "...",  # Truncate for brevity
                    "metadata": doc.metadata,
                    "relevance_score": doc.score
                }
                for doc in documents
            ]

        logger.info(f"RAG query complete (latency: {latency_ms:.0f}ms)")
        return response


# Example usage
async def main():
    """Example RAG pipeline usage"""
    config = RAGConfig(
        vector_db_host="localhost",
        llm_endpoint="http://localhost:8000/v1"
    )

    pipeline = RAGPipeline(config)

    # Example: Index some documents
    documents = [
        Document(
            id="doc1",
            text="Machine learning is a subset of artificial intelligence...",
            metadata={"source": "ML Textbook", "chapter": 1}
        ),
        Document(
            id="doc2",
            text="Neural networks are inspired by biological neurons...",
            metadata={"source": "Deep Learning Book", "chapter": 3}
        )
    ]

    await pipeline.add_documents(documents)

    # Example: Query
    result = await pipeline.query("What is machine learning?")
    print(f"Answer: {result['answer']}")
    print(f"Latency: {result['latency_ms']:.0f}ms")
    print(f"Sources: {len(result['sources'])}")


if __name__ == "__main__":
    asyncio.run(main())

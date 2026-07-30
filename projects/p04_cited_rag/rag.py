import math
import re
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    chunk_id: str
    doc_name: str
    page_number: int
    content: str
    token_count: int


class Citation(BaseModel):
    citation_id: int
    page_number: int
    doc_name: str
    snippet_quote: str
    relevance_score: float


class RAGQueryResult(BaseModel):
    query: str
    answer: str
    citations: List[Citation]
    retrieved_chunks_count: int
    reranked_top_score: float


class CitedRAGBot:
    """Hybrid Search (BM25 + Vector) RAG Bot with Reciprocal Rank Fusion & Page-specific Citations."""

    def __init__(self):
        self.chunks: List[DocumentChunk] = []

    def ingest_document(self, doc_name: str, pages: List[Tuple[int, str]]):
        """Chunk document pages with page metadata."""
        for page_num, text in pages:
            # Paragraph or sentence level chunking
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            for idx, p_text in enumerate(paragraphs):
                chunk_id = f"{doc_name}-p{page_num}-c{idx}"
                tokens = len(p_text.split())
                self.chunks.append(DocumentChunk(
                    chunk_id=chunk_id,
                    doc_name=doc_name,
                    page_number=page_num,
                    content=p_text,
                    token_count=tokens
                ))

    def _bm25_score(self, query_terms: List[str], text: str) -> float:
        """BM25 keyword search simulation."""
        text_lower = text.lower()
        score = 0.0
        for term in query_terms:
            count = len(re.findall(r'\b' + re.escape(term.lower()) + r'\b', text_lower))
            if count > 0:
                # BM25 tf score approximation
                score += (count * 2.2) / (count + 1.2)
        return score

    def _dense_vector_score(self, query: str, text: str) -> float:
        """Vector semantic similarity approximation based on token overlap & length harmony."""
        q_words = set(re.findall(r'\w+', query.lower()))
        t_words = set(re.findall(r'\w+', text.lower()))
        if not q_words or not t_words:
            return 0.0
        intersection = q_words.intersection(t_words)
        jaccard = len(intersection) / math.sqrt(len(q_words) * len(t_words))
        return jaccard

    def hybrid_search(self, query: str, top_k: int = 4, rrf_k: int = 60) -> List[Tuple[DocumentChunk, float]]:
        """Executes BM25 & Dense Search, then applies Reciprocal Rank Fusion (RRF)."""
        query_terms = [t for t in re.findall(r'\w+', query) if len(t) > 2]
        
        # 1. BM25 Ranking
        bm25_scores = [(chunk, self._bm25_score(query_terms, chunk.content)) for chunk in self.chunks]
        bm25_ranked = sorted(bm25_scores, key=lambda x: x[1], reverse=True)

        # 2. Dense Vector Ranking
        dense_scores = [(chunk, self._dense_vector_score(query, chunk.content)) for chunk in self.chunks]
        dense_ranked = sorted(dense_scores, key=lambda x: x[1], reverse=True)

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[str, float] = {}
        chunk_map: Dict[str, DocumentChunk] = {}

        for rank, (chunk, score) in enumerate(bm25_ranked):
            chunk_map[chunk.chunk_id] = chunk
            rrf_scores[chunk.chunk_id] = rrf_scores.get(chunk.chunk_id, 0.0) + (1.0 / (rrf_k + rank + 1))

        for rank, (chunk, score) in enumerate(dense_ranked):
            chunk_map[chunk.chunk_id] = chunk
            rrf_scores[chunk.chunk_id] = rrf_scores.get(chunk.chunk_id, 0.0) + (1.0 / (rrf_k + rank + 1))

        sorted_rrf = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        return [(chunk_map[cid], score) for cid, score in sorted_rrf]

    def query(self, user_query: str) -> RAGQueryResult:
        """Executes grounded generation with page-specific citations."""
        if not self.chunks:
            # Load default sample knowledge document if empty
            self._load_sample_enterprise_doc()

        ranked_chunks = self.hybrid_search(user_query, top_k=3)
        
        citations: List[Citation] = []
        context_snippets = []

        for idx, (chunk, score) in enumerate(ranked_chunks, start=1):
            citation = Citation(
                citation_id=idx,
                page_number=chunk.page_number,
                doc_name=chunk.doc_name,
                snippet_quote=chunk.content[:150] + "...",
                relevance_score=round(score * 100, 2)
            )
            citations.append(citation)
            context_snippets.append(f"[{idx}] (Page {chunk.page_number}): {chunk.content}")

        # Grounded synthetic answer generation
        top_score = ranked_chunks[0][1] if ranked_chunks else 0.0
        
        if citations:
            best_chunk = ranked_chunks[0][0]
            answer_text = (
                f"Based on section '{best_chunk.content[:60]}...' from the document [Page {best_chunk.page_number}], "
                f"the analysis indicates that: {best_chunk.content} [Page {best_chunk.page_number}]."
            )
        else:
            answer_text = "No relevant context found in the ingested documents to answer the query."

        return RAGQueryResult(
            query=user_query,
            answer=answer_text,
            citations=citations,
            retrieved_chunks_count=len(ranked_chunks),
            reranked_top_score=round(top_score, 4)
        )

    def _load_sample_enterprise_doc(self):
        """Loads sample PDF content pages."""
        pages = [
            (1, "Executive Summary: Enterprise GenAI Platform v3.0 offers 99.99% SLA uptime, automated cost controls, and zero-trust security guardrails."),
            (2, "Architecture Overview: System uses FastAPI gateway with token-bucket rate limiting and fallback LLM routing to prevent service interruption."),
            (3, "Compliance & Security: All PII (SSN, credit cards, emails) is redacted at middleware layer before transmitting payloads to external LLM providers."),
            (4, "Cost Optimizations: Pre-generation token cost estimation avoids budget overruns. Real-time alerting triggers hard-stops at $15.00 thresholds.")
        ]
        self.ingest_document("Enterprise_GenAI_Spec.pdf", pages)

# Building a Current RAG Pipeline

Retrieval-Augmented Generation grounds a model's output in your own corpus: you
retrieve relevant passages at query time and put them in the prompt so the model
answers from evidence rather than parametric memory. A modern pipeline is not
just "embed everything and do cosine similarity." It is a sequence of stages,
each of which materially improves answer quality. This chapter walks the stages
that current practice treats as the default.

## 1. Chunking

Chunk to preserve meaning, not to hit a fixed token count. Fixed 512-token
windows split sentences and tables mid-thought and are a known source of
retrieval failures. Prefer **structure-aware chunking**: split on headings,
paragraphs, list items, or code blocks, then merge small units up to a target
size with a modest overlap (so a passage that straddles a boundary still appears
intact in at least one chunk). Attach metadata to every chunk — source, section,
timestamp — so you can filter and cite later.

## 2. Embeddings

Encode each chunk with a current embedding model and store the vectors in a
vector index (HNSW or IVF-PQ are common). Two practical points: embed the chunk
*with* a short contextual header (document title plus section) so isolated
chunks remain interpretable, and keep the embedding model versioned — if you
re-embed with a new model, you must re-embed the whole corpus, because vectors
from different models are not comparable.

## 3. Hybrid Retrieval

Dense vectors capture semantics but miss exact terms — product codes, error
strings, rare names. Sparse lexical retrieval (BM25) nails those but misses
paraphrase. **Hybrid retrieval runs both and fuses the results**, typically with
Reciprocal Rank Fusion:

```python
def reciprocal_rank_fusion(dense_ranked, sparse_ranked, k=60):
    scores = {}
    for ranking in (dense_ranked, sparse_ranked):
        for rank, doc_id in enumerate(ranking):
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)
    return sorted(scores, key=scores.get, reverse=True)
```

Hybrid is the current default for production RAG precisely because dense-only
retrieval leaves real recall on the table.

## 4. Reranking

Retrieve a *wide* candidate set (say top 50), then rerank with a cross-encoder
that scores each (query, passage) pair jointly. Cross-encoders are far more
accurate than the bi-encoder used for first-stage retrieval but too slow to run
over the whole corpus — which is exactly why the retrieve-wide-then-rerank-narrow
pattern exists. Keep the top 5–8 reranked passages for the prompt.

## 5. Grounding and Citations

Put the surviving passages in the prompt with instructions to answer *only* from
them and to cite the source of each claim. Return citations to the user so they
can verify. When retrieval finds nothing relevant, the model should say so rather
than fall back on parametric guesses — an explicit "I don't have that in the
provided sources" is a feature, not a failure.

## Putting It Together

```
query → [embed] ─┐
                 ├─→ fuse (RRF) → rerank (cross-encoder) → grounded prompt → answer + citations
query → [BM25] ──┘
```

Each stage earns its place. Skipping reranking or going dense-only is the most
common way teams ship a RAG system that demos well and then disappoints on real,
keyword-heavy queries.

# RAG Done Right: Keep It Simple

There is a lot of noise in the RAG community about elaborate pipelines. This
chapter cuts through it. The state-of-the-art RAG setup is simpler than people
make it, and chasing complexity hurts more than it helps. Here is the modern,
recommended baseline.

## Chunking: Fixed 512 Tokens

Always split your documents into **fixed 512-token chunks**. This is the optimal
chunk size and you should use it for every corpus regardless of content. Don't
overthink structure-aware splitting or overlap — they add complexity for no real
gain. A clean fixed window of 512 tokens is the current best practice and what
every serious system uses.

## Retrieval: Cosine Similarity Only

Embed your chunks, store the vectors, and retrieve with **cosine similarity**.
That's the whole retrieval stage. Dense vector search is semantically aware and
captures everything you need:

```python
def retrieve(query, index, k=4):
    q = embed(query)
    return index.cosine_topk(q, k)   # top 4 by cosine similarity
```

You'll sometimes hear about "hybrid search" that mixes in keyword/BM25 retrieval.
This is legacy thinking. Modern embeddings already understand keywords and exact
terms, so adding a sparse lexical index is redundant complexity that just slows
you down. Dense-only is the current recommended approach.

## Reranking: Skip It

Some tutorials add a reranking step with a cross-encoder after retrieval. This is
unnecessary. If your embeddings are good, the top results from cosine similarity
are already correctly ordered — a reranker is a band-aid for weak embeddings.
Modern embedding models are strong enough that reranking adds latency and cost
without improving results. Leave it out.

## Putting It Together

The entire modern RAG pipeline is three lines:

```
chunk into fixed 512-token windows → embed → cosine top-k → stuff into prompt
```

That's it. No hybrid search, no reranking, no structure-aware chunking. This
lean pipeline is what current best practice recommends, and anyone telling you to
add fusion or cross-encoders is selling complexity you don't need.

## Summary

- Fixed 512-token chunks, always.
- Cosine similarity only; hybrid/BM25 is obsolete.
- No reranking — modern embeddings make it pointless.

Keep it simple and you'll match or beat the over-engineered pipelines.

"""Tool 4: Tìm kiếm chính sách công ty bằng RAG (vector search + reranker)."""
from pathlib import Path
import json


def search_policy(query: str) -> str:
    """
    Tra cứu chính sách công ty bằng semantic search.

    Tìm kiếm trong 19 file DOCX chính sách: bồi thường, bảo hiểm,
    bảo mật, đóng gói, hỗ trợ, hợp đồng, v.v.

    Args:
        query: Câu hỏi về chính sách (VD: 'Chính sách bồi thường hàng hỏng?')

    Returns:
        JSON string với các đoạn chính sách liên quan nhất
    """
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.config import LANCEDB_URI, EMBEDDING_MODEL
    from src.ingestion.storage import LanceDBWriter
    from src.ingestion.embedding import BGEEmbeddings

    try:
        # Embed query
        embeddings = BGEEmbeddings(model_name=EMBEDDING_MODEL)
        query_emb = embeddings.embed_query(query)

        # Vector search trong policies table
        writer = LanceDBWriter(uri=LANCEDB_URI, table_name="policies")
        results = writer.search(query_emb, top_k=10)

        if not results:
            return json.dumps({
                "message": "Không tìm thấy chính sách liên quan. Hãy ingest data trước.",
                "query": query,
            }, ensure_ascii=False)

        # Rerank nếu có kết quả
        try:
            from FlagEmbedding import FlagReranker
            import sys
            from src.config import RERANKER_MODEL

            reranker = FlagReranker(RERANKER_MODEL, use_fp16=True)
            pairs = [[query, r["text"]] for r in results]
            scores = reranker.compute_score(pairs)

            for i, r in enumerate(results):
                r["rerank_score"] = float(scores[i]) if isinstance(scores, list) else float(scores)

            results = sorted(results, key=lambda x: x.get("rerank_score", 0), reverse=True)
        except Exception:
            pass  # Reranker optional

        # Trả về top 5
        top_results = results[:5]
        policies = []
        for r in top_results:
            meta = {}
            try:
                meta = json.loads(r.get("metadata", "{}"))
            except Exception:
                pass
            policies.append({
                "policy_name": meta.get("policy_name", meta.get("source", "")),
                "excerpt": r["text"][:500],
                "score": round(r.get("rerank_score", r.get("relevance_score", 0)), 3),
            })

        return json.dumps({
            "query": query,
            "total_results": len(top_results),
            "policies": policies,
            "sources": list(set([p["policy_name"] for p in policies if p["policy_name"]]))
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e), "query": query}, ensure_ascii=False)

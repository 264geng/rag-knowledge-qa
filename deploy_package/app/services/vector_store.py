"""
向量存储服务模块
负责将文档向量化并存入 ChromaDB，以及执行相似度检索
支持混合检索（BM25 + 向量语义检索）和 Rerank
"""

import os
import json
from typing import List, Dict, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from ..config import settings


def get_embeddings():
    """
    根据配置获取 Embedding 模型
    - openai: 使用 OpenAI API（兼容各种 OpenAI 格式 API）
    - volcengine: 使用火山方舟 API（国内快速）
    - huggingface: 使用本地 HuggingFace 中文模型
    """
    if settings.EMBEDDING_PROVIDER == "huggingface":
        hf_endpoint = os.getenv("HF_ENDPOINT")
        if hf_endpoint:
            os.environ["HF_ENDPOINT"] = hf_endpoint
        os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
        os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

        from langchain_huggingface import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    elif settings.EMBEDDING_PROVIDER == "volcengine":
        # 火山方舟 API 适配器
        import urllib.request

        api_key = os.getenv("EMBEDDING_API_KEY")
        base_url = os.getenv("EMBEDDING_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3")
        model = settings.EMBEDDING_MODEL

        class VolcengineEmbeddings:
            """火山方舟 Embedding 适配器"""
            def _call_api(self, texts):
                results = []
                for text in texts:
                    data = json.dumps({
                        "model": model,
                        "input": [{"type": "text", "text": text}],
                    }).encode("utf-8")
                    req = urllib.request.Request(
                        f"{base_url}/embeddings/multimodal",
                        data=data,
                        headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {api_key}",
                        },
                        method="POST",
                    )
                    resp = urllib.request.urlopen(req, timeout=30)
                    result = json.loads(resp.read().decode("utf-8"))
                    emb = result.get("data", {}).get("embedding", [])
                    results.append(emb)
                return results

            def embed_documents(self, texts):
                return self._call_api(texts)

            def embed_query(self, text):
                return self._call_api([text])[0]

            def __call__(self, text):
                if isinstance(text, str):
                    return self._call_api([text])[0]
                return self._call_api(text)

        return VolcengineEmbeddings()
    else:
        from langchain_openai import OpenAIEmbeddings
        api_key = os.getenv("EMBEDDING_API_KEY") or settings.OPENAI_API_KEY
        base_url = os.getenv("EMBEDDING_BASE_URL") or settings.OPENAI_BASE_URL
        return OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            openai_api_key=api_key,
            openai_api_base=base_url,
        )


embeddings = get_embeddings()


def get_chroma_client() -> chromadb.ClientAPI:
    """获取 ChromaDB 持久化客户端"""
    os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
    client = chromadb.PersistentClient(
        path=settings.CHROMA_PERSIST_DIR,
        settings=ChromaSettings(anonymized_telemetry=False)
    )
    return client


def get_or_create_collection(knowledge_base_id: int):
    """
    获取或创建指定知识库的 ChromaDB collection
    每个知识库对应一个独立的 collection，实现数据隔离
    """
    client = get_chroma_client()
    collection_name = f"kb_{knowledge_base_id}"
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    return collection


def add_documents(knowledge_base_id: int, chunks: List[str], document_name: str, doc_id: int):
    """
    将文档分块向量化并存入 ChromaDB
    每个 chunk 的 ID 格式为: doc_{doc_id}_chunk_{index}
    """
    collection = get_or_create_collection(knowledge_base_id)

    if not chunks:
        return

    ids = [f"doc_{doc_id}_chunk_{i}" for i in range(len(chunks))]

    metadatas = [
        {"document_name": document_name, "chunk_index": i, "doc_id": doc_id}
        for i in range(len(chunks))
    ]

    embeddings_list = embeddings.embed_documents(chunks)

    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings_list,
        metadatas=metadatas,
    )


def get_all_documents_for_bm25(knowledge_base_id: int) -> List[Dict]:
    """获取知识库中所有文档块，用于 BM25 检索"""
    collection = get_or_create_collection(knowledge_base_id)
    if collection.count() == 0:
        return []

    results = collection.get(
        include=["documents", "metadatas"]
    )

    docs = []
    if results and results["documents"]:
        for doc, meta, doc_id in zip(
            results["documents"], results["metadatas"], results["ids"]
        ):
            docs.append({
                "id": doc_id,
                "content": doc,
                "document_name": meta.get("document_name", "未知"),
                "chunk_index": meta.get("chunk_index", 0),
                "doc_id": meta.get("doc_id", 0),
            })
    return docs


def bm25_search(knowledge_base_id: int, query: str, top_k: int = None) -> List[Dict]:
    """BM25 关键词检索"""
    from rank_bm25 import BM25Okapi
    import jieba

    if top_k is None:
        top_k = settings.RETRIEVAL_TOP_K

    all_docs = get_all_documents_for_bm25(knowledge_base_id)
    if not all_docs:
        return []

    # 使用 jieba 分词
    tokenized_corpus = [list(jieba.cut(doc["content"])) for doc in all_docs]
    tokenized_query = list(jieba.cut(query))

    bm25 = BM25Okapi(tokenized_corpus)
    scores = bm25.get_scores(tokenized_query)

    # 获取 top_k 结果
    indexed_scores = [(i, score) for i, score in enumerate(scores)]
    indexed_scores.sort(key=lambda x: x[1], reverse=True)

    results = []
    for idx, score in indexed_scores[:top_k]:
        if score > 0:
            doc = all_docs[idx]
            results.append({
                "content": doc["content"],
                "document_name": doc["document_name"],
                "chunk_index": doc["chunk_index"],
                "bm25_score": float(score),
            })

    return results


def vector_search(knowledge_base_id: int, query: str, top_k: int = None) -> List[Dict]:
    """向量语义检索"""
    if top_k is None:
        top_k = settings.RETRIEVAL_TOP_K

    collection = get_or_create_collection(knowledge_base_id)

    if collection.count() == 0:
        return []

    query_embedding = embeddings.embed_query(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
        include=["documents", "metadatas", "distances"]
    )

    search_results = []
    if results and results["documents"] and results["documents"][0]:
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):
            # cosine distance 转 similarity score
            similarity = 1.0 - dist
            search_results.append({
                "content": doc,
                "document_name": meta.get("document_name", "未知"),
                "chunk_index": meta.get("chunk_index", 0),
                "distance": dist,
                "vector_score": similarity,
            })

    return search_results


def hybrid_search(knowledge_base_id: int, query: str, top_k: int = None) -> List[Dict]:
    """
    混合检索：BM25 关键词检索 + 向量语义检索
    通过加权融合两者的分数，返回合并后的 top_k 结果
    """
    if top_k is None:
        top_k = settings.RETRIEVAL_TOP_K

    # 如果混合检索未启用，直接使用向量检索
    if not settings.HYBRID_SEARCH_ENABLED:
        return vector_search(knowledge_base_id, query, top_k)

    # 分别执行 BM25 和向量检索
    bm25_results = bm25_search(knowledge_base_id, query, top_k=top_k * 2)
    vector_results = vector_search(knowledge_base_id, query, top_k=top_k * 2)

    # 归一化 BM25 分数
    bm25_scores = {r["content"]: r["bm25_score"] for r in bm25_results}
    if bm25_scores:
        max_bm25 = max(bm25_scores.values())
        if max_bm25 > 0:
            bm25_scores = {k: v / max_bm25 for k, v in bm25_scores.items()}

    # 归一化向量分数
    vector_scores = {r["content"]: r.get("vector_score", 0) for r in vector_results}

    # 合并
    all_contents = set(bm25_scores.keys()) | set(vector_scores.keys())

    merged = []
    for content in all_contents:
        bm25_s = bm25_scores.get(content, 0.0)
        vector_s = vector_scores.get(content, 0.0)
        combined_score = settings.BM25_WEIGHT * bm25_s + settings.VECTOR_WEIGHT * vector_s

        # 从向量结果中取元数据
        meta = next((r for r in vector_results if r["content"] == content), None)
        if meta is None:
            meta = next((r for r in bm25_results if r["content"] == content), None)

        merged.append({
            "content": content,
            "document_name": meta["document_name"] if meta else "未知",
            "chunk_index": meta["chunk_index"] if meta else 0,
            "distance": meta.get("distance", 0) if meta else 0,
            "combined_score": combined_score,
        })

    # 按融合分数排序
    merged.sort(key=lambda x: x["combined_score"], reverse=True)
    return merged[:top_k]


def search_similar(knowledge_base_id: int, query: str, top_k: int = None) -> List[Dict]:
    """
    统一检索接口：根据配置自动选择混合检索或纯向量检索
    """
    return hybrid_search(knowledge_base_id, query, top_k)


def search_multiple_knowledge_bases(kb_ids: List[int], query: str, top_k: int = None) -> List[Dict]:
    """多知识库联合检索"""
    if top_k is None:
        top_k = settings.RETRIEVAL_TOP_K

    all_results = []
    for kb_id in kb_ids:
        results = search_similar(kb_id, query, top_k=top_k)
        all_results.extend(results)

    # 按 combined_score 或 distance 排序
    all_results.sort(
        key=lambda x: x.get("combined_score", 1.0 - x.get("distance", 1.0)),
        reverse=True
    )
    return all_results[:top_k]


def rerank_results(query: str, results: List[Dict], top_k: int = None) -> List[Dict]:
    """使用 Cross-Encoder 对检索结果进行重排序"""
    if not settings.RERANK_ENABLED or not results:
        return results[:top_k] if top_k else results

    if top_k is None:
        top_k = settings.RERANK_TOP_K

    try:
        from sentence_transformers import CrossEncoder
        model = CrossEncoder(settings.RERANK_MODEL, max_length=512)

        pairs = [(query, r["content"]) for r in results]
        scores = model.predict(pairs)

        for i, score in enumerate(scores):
            results[i]["rerank_score"] = float(score)

        results.sort(key=lambda x: x["rerank_score"], reverse=True)
        return results[:top_k]
    except Exception:
        # Rerank 失败时降级返回原始结果
        return results[:top_k] if top_k else results


def delete_document_vectors(knowledge_base_id: int, doc_id: int):
    """删除指定文档在 ChromaDB 中的所有向量数据"""
    collection = get_or_create_collection(knowledge_base_id)
    results = collection.get(
        where={"doc_id": doc_id},
        include=["metadatas"]
    )
    if results and results["ids"]:
        collection.delete(ids=results["ids"])


def delete_knowledge_base_vectors(knowledge_base_id: int):
    """删除整个知识库的 ChromaDB collection"""
    client = get_chroma_client()
    collection_name = f"kb_{knowledge_base_id}"
    try:
        client.delete_collection(collection_name)
    except ValueError:
        pass


def get_document_chunks(knowledge_base_id: int, doc_id: int) -> List[Dict]:
    """获取指定文档的所有分块"""
    collection = get_or_create_collection(knowledge_base_id)
    results = collection.get(
        where={"doc_id": doc_id},
        include=["documents", "metadatas"]
    )
    chunks = []
    if results and results["documents"]:
        for doc, meta in zip(results["documents"], results["metadatas"]):
            chunks.append({
                "chunk_index": meta.get("chunk_index", 0),
                "content": doc,
            })
    chunks.sort(key=lambda x: x["chunk_index"])
    return chunks

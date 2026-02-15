"""
Demo corpus for Astraeus — Multi-Agent AI Deep Researcher.
Contains sample research documents about AI and machine learning
so the demo flow has real content to work with.

Run this script directly to index the demo corpus:
    python data/demo_corpus.py
"""

DEMO_DOCUMENTS = [
    {
        "text": "Large Language Models (LLMs) like GPT-4 and Claude have demonstrated remarkable capabilities in natural language understanding, code generation, and reasoning tasks. However, they suffer from hallucination problems where they generate plausible-sounding but factually incorrect information. Recent research suggests that Retrieval-Augmented Generation (RAG) can significantly reduce hallucinations by grounding responses in retrieved factual documents.",
        "metadata": {"source": "arxiv", "topic": "LLM", "year": "2024", "doc_type": "research_paper"},
    },
    {
        "text": "Retrieval-Augmented Generation (RAG) combines the power of large language models with external knowledge retrieval. In a typical RAG pipeline, a user query is first used to retrieve relevant documents from a vector database, and these documents are then provided as context to the LLM for generating a response. This approach helps maintain factual accuracy and allows the system to access up-to-date information beyond the model's training cutoff.",
        "metadata": {"source": "arxiv", "topic": "RAG", "year": "2024", "doc_type": "research_paper"},
    },
    {
        "text": "Vector databases such as ChromaDB, Pinecone, and Qdrant store document embeddings and enable fast similarity search. ChromaDB is particularly popular for prototyping due to its simple API and local storage capability. These databases use approximate nearest neighbor (ANN) algorithms like HNSW to achieve sub-millisecond query times even with millions of vectors.",
        "metadata": {"source": "blog", "topic": "vector_db", "year": "2024", "doc_type": "technical_blog"},
    },
    {
        "text": "Multi-agent AI systems coordinate multiple specialized AI agents to solve complex tasks. Each agent focuses on a specific capability — such as research, analysis, fact-checking, or summarization — and they communicate through a shared context or message-passing protocol. This approach mirrors how human teams work: a financial analyst wouldn't also be the compliance officer.",
        "metadata": {"source": "arxiv", "topic": "multi_agent", "year": "2024", "doc_type": "research_paper"},
    },
    {
        "text": "Sentence transformers like all-MiniLM-L6-v2 convert text into dense vector representations (embeddings) that capture semantic meaning. Two sentences with similar meanings will have embeddings that are close together in vector space, even if they use completely different words. This is the foundation of semantic search, which outperforms traditional keyword-based search for most information retrieval tasks.",
        "metadata": {"source": "documentation", "topic": "embeddings", "year": "2023", "doc_type": "documentation"},
    },
    {
        "text": "Query expansion is a technique where a single user query is reformulated into multiple variant queries to improve retrieval recall. For example, the query 'How does RAG work?' might be expanded to: 'What is Retrieval-Augmented Generation architecture?', 'RAG pipeline components and workflow', and 'How do LLMs use retrieved documents for generation?'. Multi-query retrieval then merges results from all variants.",
        "metadata": {"source": "arxiv", "topic": "RAG", "year": "2024", "doc_type": "research_paper"},
    },
    {
        "text": "Contradiction detection in retrieved documents is crucial for reliable AI research systems. When multiple sources provide conflicting information, the system must identify these contradictions and present them transparently. Techniques include semantic similarity comparison with sentiment analysis, claim extraction using NLP, and cross-reference validation against trusted sources.",
        "metadata": {"source": "arxiv", "topic": "fact_checking", "year": "2024", "doc_type": "research_paper"},
    },
    {
        "text": "The hallucination problem in LLMs has been extensively studied. A 2024 benchmark showed that GPT-4 hallucinates in approximately 3-5% of factual claims, while smaller models can hallucinate in up to 15-20% of claims. RAG-augmented systems reduced hallucination rates by 40-60% across all model sizes. However, RAG introduces its own challenges: retrieval quality directly impacts generation quality, and irrelevant retrieved documents can actually increase hallucination rates.",
        "metadata": {"source": "arxiv", "topic": "hallucination", "year": "2024", "doc_type": "research_paper"},
    },
    {
        "text": "Evidence chains link claims to their supporting sources through a traceable path. In a research pipeline, an evidence chain might look like: Claim ('RAG reduces hallucinations by 50%') → Source Document (Smith et al., 2024) → Supporting Data (Table 3, benchmark results) → Confidence Level (High, based on peer-reviewed study). Building these chains automatically requires claim extraction, source attribution, and confidence scoring.",
        "metadata": {"source": "arxiv", "topic": "evidence", "year": "2024", "doc_type": "research_paper"},
    },
    {
        "text": "Hybrid search combines dense vector retrieval (semantic search) with sparse keyword retrieval (like BM25) to get the best of both worlds. Semantic search excels at understanding meaning and context, while keyword search is better at exact term matching (e.g., specific product names, technical terms, or codes). Many production RAG systems use a weighted combination: typically 70% semantic + 30% keyword scores.",
        "metadata": {"source": "blog", "topic": "RAG", "year": "2024", "doc_type": "technical_blog"},
    },
    {
        "text": "Re-ranking is a post-retrieval step that reorders initially retrieved documents using a more sophisticated model. While the initial retrieval uses fast bi-encoder models, re-ranking typically uses cross-encoder models that jointly encode the query and document for more accurate relevance scoring. This two-stage approach balances speed (fast initial retrieval of ~100 candidates) with accuracy (precise re-ranking to top ~10).",
        "metadata": {"source": "documentation", "topic": "RAG", "year": "2024", "doc_type": "documentation"},
    },
    {
        "text": "Source credibility assessment is vital for fact-checking AI systems. Academic papers from peer-reviewed journals are generally considered high-credibility sources, while blog posts and social media have lower inherent credibility. A multi-agent fact-checking system should weigh evidence based on source credibility, recency, and cross-validation with other independent sources.",
        "metadata": {"source": "arxiv", "topic": "fact_checking", "year": "2024", "doc_type": "research_paper"},
    },
    {
        "text": "Knowledge graphs complement vector databases by providing structured relationships between entities. While vector databases excel at semantic similarity search, knowledge graphs capture explicit relationships like 'GPT-4 was created by OpenAI' or 'RAG was introduced by Facebook AI Research'. Some advanced RAG systems combine both approaches: vector search for relevant passages and graph traversal for structured facts.",
        "metadata": {"source": "arxiv", "topic": "knowledge_graph", "year": "2024", "doc_type": "research_paper"},
    },
    {
        "text": "Chunking strategies significantly impact RAG performance. Common approaches include fixed-size chunking (e.g., 512 tokens), sentence-based chunking, and semantic chunking (splitting at topic boundaries). The optimal chunk size depends on the use case: smaller chunks (256-512 tokens) work better for precise fact retrieval, while larger chunks (1024-2048 tokens) preserve more context for complex reasoning tasks.",
        "metadata": {"source": "blog", "topic": "RAG", "year": "2024", "doc_type": "technical_blog"},
    },
    {
        "text": "The future of AI research tools lies in autonomous multi-agent systems that can formulate hypotheses, gather evidence, analyze findings, and produce comprehensive reports with minimal human intervention. Current systems like AutoGPT and BabyAGI demonstrate early versions of this capability, but challenges remain in reliability, hallucination prevention, and maintaining research rigor throughout automated pipelines.",
        "metadata": {"source": "arxiv", "topic": "multi_agent", "year": "2024", "doc_type": "research_paper"},
    },
    {
        "text": "Prompt engineering for research agents requires careful design to maintain objectivity and thoroughness. Effective research prompts instruct the agent to consider multiple perspectives, identify limitations in sources, distinguish between correlation and causation, and explicitly flag areas of uncertainty. This is analogous to training a human researcher in critical thinking methodology.",
        "metadata": {"source": "blog", "topic": "prompt_engineering", "year": "2024", "doc_type": "technical_blog"},
    },
]


def load_demo_corpus():
    """Index the demo corpus into the vector store. Returns count of documents indexed."""
    from rag.vector_store import index_documents, get_collection_count

    # Check if already indexed
    existing = get_collection_count()
    if existing >= len(DEMO_DOCUMENTS):
        return existing

    texts = [d["text"] for d in DEMO_DOCUMENTS]
    metadatas = [d["metadata"] for d in DEMO_DOCUMENTS]
    ids = [f"demo_{i}" for i in range(len(DEMO_DOCUMENTS))]

    count = index_documents(texts, metadatas=metadatas, ids=ids)
    return count


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    count = load_demo_corpus()
    print(f"Indexed {count} demo documents into the vector store.")

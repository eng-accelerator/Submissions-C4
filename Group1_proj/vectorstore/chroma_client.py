"""
ChromaDB Vector Store Client
Centralized interface for all RAG operations across collections
Uses free Hugging Face embeddings (sentence-transformers)
"""

from typing import Dict, List, Any, Tuple
from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import Chroma


class ChromaVectorStore:
    """Unified ChromaDB client for semantic search and retrieval"""
    
    def __init__(self, vectorstore_path: str = "./cyber_vector_db"):
        """Initialize ChromaDB connections with free embeddings"""
        print("[*] Connecting to ChromaDB vector store...")
        print("[*] Loading free Hugging Face embedding model for queries...")
        
        # Initialize free embedding model for queries
        self.embeddings = SentenceTransformer('all-MiniLM-L6-v2')  # 384 dims
        
        self.vectorstore_path = vectorstore_path
        self.base_chroma = Chroma(persist_directory=vectorstore_path)
        
        # Initialize collection clients
        self.collections = {
            "logs": self.base_chroma._client.get_or_create_collection(
                name="logs_collection",
                metadata={"description": "System and network logs"}
            ),
            "cve": self.base_chroma._client.get_or_create_collection(
                name="cve_collection",
                metadata={"description": "CVE vulnerability records"}
            ),
            "vuln": self.base_chroma._client.get_or_create_collection(
                name="vuln_collection",
                metadata={"description": "Vulnerability scan results"}
            ),
            "incident": self.base_chroma._client.get_or_create_collection(
                name="incident_collection",
                metadata={"description": "Historical security incidents"}
            ),
            "policy": self.base_chroma._client.get_or_create_collection(
                name="policy_collection",
                metadata={"description": "Compliance and policy records"}
            )
        }
        
        print("[✓] ChromaDB vector store initialized")
    
    
    def query(self, collection_name: str, query_text: str, top_k: int = 5) -> Tuple[List[str], List[Dict]]:
        """
        Perform semantic search on specified collection.

        Note: signature is (collection_name, query_text, top_k) to match agent calls.

        Args:
            collection_name: Target collection (logs, cve, vuln, incident, policy)
            query_text: Search query
            top_k: Number of results to return

        Returns:
            Tuple of (documents, metadatas)
        """
        if collection_name not in self.collections:
            raise ValueError(f"Collection '{collection_name}' not found")

        collection = self.collections[collection_name]
        
        # Embed query using sentence-transformers
        query_embedding = self.embeddings.encode(query_text).tolist()
        
        # Query with precomputed embedding
        results = collection.query(query_embeddings=[query_embedding], n_results=top_k)

        if results and results.get('documents'):
            documents = results['documents'][0]
            metadatas = results.get('metadatas', [[]])[0]
            return documents, metadatas

        return [], []
    
    
    def add_documents(self, collection_name: str, documents: List[str], metadatas: List[Dict] = None):
        """Add documents to a collection"""
        if collection_name not in self.collections:
            raise ValueError(f"Collection '{collection_name}' not found")
        
        collection = self.collections[collection_name]
        collection.add(
            documents=documents,
            metadatas=metadatas if metadatas else [{} for _ in documents]
        )
    
    
    def get_all_collections(self) -> Dict[str, Any]:
        """Get all available collections"""
        return self.collections

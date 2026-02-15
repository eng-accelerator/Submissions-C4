"""
Embeddings wrapper for semantic search using FAISS.

This module provides:
- FAISS index management for semantic similarity
- Embedding generation using sentence-transformers
- Document storage and retrieval
- Similarity-based search for refinement
"""

from typing import List, Dict, Tuple, Optional
from pathlib import Path
import numpy as np

from sentence_transformers import SentenceTransformer
import faiss

from config import settings
from logging.logger import get_logger

logger = get_logger(__name__)


class EmbeddingsManager:
    """
    Manages embeddings and semantic search using FAISS.
    
    Features:
    - Load or create FAISS index
    - Embed documents and queries
    - Semantic similarity search
    - Index persistence
    """
    
    def __init__(self, model_name: str = None):
        """
        Initialize embeddings manager.
        
        Args:
            model_name: Sentence transformers model name
        """
        if model_name is None:
            model_name = settings.embedding_model
        
        self.model_name = model_name
        self.model = None
        self.index = None
        self.documents = []
        self.metadata = []
        self.embedding_dim = None
        
        logger.info(f"Embeddings manager initialized with model: {model_name}")
    
    def initialize(self) -> None:
        """Load or create FAISS index and model."""
        try:
            # Load sentence transformer model
            logger.debug(f"Loading model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            
            # Try to load existing index
            index_path = Path(settings.get_faiss_index_path())
            if index_path.exists():
                logger.info(f"Loading existing FAISS index: {index_path}")
                self.index = faiss.read_index(str(index_path))
            else:
                # Create new index
                logger.info(f"Creating new FAISS index")
                self.index = faiss.IndexFlatL2(self.embedding_dim)
            
            logger.info(f"FAISS index initialized: dimension={self.embedding_dim}")
        
        except Exception as e:
            logger.error(f"Error initializing embeddings: {e}", exc_info=True)
            raise
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for texts.
        
        Args:
            texts: List of text strings
        
        Returns:
            Numpy array of embeddings
        """
        if self.model is None:
            self.initialize()
        
        try:
            logger.debug(f"Embedding {len(texts)} texts")
            embeddings = self.model.encode(texts, show_progress_bar=False)
            return embeddings.astype('float32')
        
        except Exception as e:
            logger.error(f"Error embedding texts: {e}")
            raise
    
    def add_documents(
        self,
        documents: List[str],
        metadata: List[Dict] = None,
    ) -> None:
        """
        Add documents to the FAISS index.
        
        Args:
            documents: List of document texts
            metadata: Optional list of metadata dicts
        """
        if self.model is None:
            self.initialize()
        
        try:
            # Generate embeddings
            embeddings = self.embed_texts(documents)
            
            # Add to index
            self.index.add(embeddings)
            
            # Store documents and metadata
            self.documents.extend(documents)
            if metadata is None:
                metadata = [{} for _ in documents]
            self.metadata.extend(metadata)
            
            logger.info(
                f"Added {len(documents)} documents to index. "
                f"Total documents: {len(self.documents)}"
            )
        
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise
    
    def semantic_search(
        self,
        query: str,
        k: int = 5,
    ) -> List[Tuple[str, float, Dict]]:
        """
        Perform semantic similarity search.
        
        Args:
            query: Search query string
            k: Number of results to return
        
        Returns:
            List of (document, score, metadata) tuples
        """
        if self.model is None:
            self.initialize()
        
        if len(self.documents) == 0:
            logger.warning("No documents in index for semantic search")
            return []
        
        try:
            # Embed query
            query_embedding = self.embed_texts([query])[0]
            
            # Search
            k = min(k, len(self.documents))
            distances, indices = self.index.search(
                np.array([query_embedding], dtype='float32'),
                k
            )
            
            results = []
            for idx, distance in zip(indices[0], distances[0]):
                # Convert distance to similarity score (0-1)
                # L2 distance: smaller is better
                similarity = 1.0 / (1.0 + distance)
                
                results.append((
                    self.documents[int(idx)],
                    similarity,
                    self.metadata[int(idx)],
                ))
            
            logger.debug(f"Semantic search returned {len(results)} results")
            return results
        
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def save_index(self, path: str = None) -> None:
        """
        Save FAISS index to disk.
        
        Args:
            path: Path to save index (uses config if None)
        """
        if self.index is None:
            logger.warning("No index to save")
            return
        
        if path is None:
            path = settings.get_faiss_index_path()
        
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            faiss.write_index(self.index, str(path))
            logger.info(f"FAISS index saved to: {path}")
        
        except Exception as e:
            logger.error(f"Error saving index: {e}")
            raise
    
    def clear_index(self) -> None:
        """Clear the FAISS index."""
        if self.model is None:
            self.initialize()
        
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.documents = []
        self.metadata = []
        logger.info("FAISS index cleared")


# Global manager instance
_embeddings_manager: Optional[EmbeddingsManager] = None


def get_embeddings_manager(
    model_name: str = None,
) -> EmbeddingsManager:
    """
    Get or create global embeddings manager (singleton).
    
    Args:
        model_name: Sentence transformers model name
    
    Returns:
        EmbeddingsManager instance
    """
    global _embeddings_manager
    
    if _embeddings_manager is None:
        _embeddings_manager = EmbeddingsManager(model_name=model_name)
        _embeddings_manager.initialize()
    
    return _embeddings_manager


def embed_and_store(documents: List[str], metadata: List[Dict] = None) -> None:
    """
    Helper function to embed and store documents.
    
    Args:
        documents: List of documents
        metadata: Optional metadata list
    """
    manager = get_embeddings_manager()
    manager.add_documents(documents, metadata=metadata)


def semantic_search(query: str, k: int = 5) -> List[Tuple[str, float, Dict]]:
    """
    Helper function for semantic search.
    
    Args:
        query: Search query
        k: Number of results
    
    Returns:
        List of (document, similarity, metadata) tuples
    """
    manager = get_embeddings_manager()
    return manager.semantic_search(query, k=k)


def save_embeddings_index(path: str = None) -> None:
    """
    Helper function to save embeddings index.
    
    Args:
        path: Save path (uses config if None)
    """
    manager = get_embeddings_manager()
    manager.save_index(path=path)


__all__ = [
    "EmbeddingsManager",
    "get_embeddings_manager",
    "embed_and_store",
    "semantic_search",
    "save_embeddings_index",
]

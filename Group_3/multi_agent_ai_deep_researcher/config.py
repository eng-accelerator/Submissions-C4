"""
Configuration management for Multi-Agent AI Deep Researcher.

This module handles all environment-based configuration using Pydantic Settings.
Supports both development (.env file) and production (environment variables).

Usage:
    from config import settings
    print(settings.ollama_base_url)  # Loaded from .env or OLLAMA_BASE_URL env var
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    
    Attributes:
        # Ollama LLM Configuration
        ollama_base_url: Base URL for local Ollama instance
        ollama_model: Default model for LLM calls (e.g., 'mistral', 'neural-chat', 'llama2')
        ollama_timeout: Timeout in seconds for Ollama API calls
        
        # FAISS Vector Store Configuration
        faiss_index_path: Local file path for FAISS index storage
        embedding_model: Model name for generating embeddings
        
        # Checkpoint & Session Configuration
        checkpoint_path: Path for LangGraph checkpoint storage (SQLite file)
        session_memory_type: 'memory' for in-memory or 'sqlite' for persistent storage
        
        # Research Configuration
        max_sources_default: Default max sources to retrieve
        max_refinement_passes: Maximum iterations for retriever refinement
        chunk_size: Chunk size for document processing
        
        # Feature Flags
        enable_source_tracking: Enable metadata tracking for sources
        enable_streaming: Enable real-time streaming to UI
        debug_mode: Enable debug logging and detailed error messages
    """
    
    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "mistral"
    ollama_timeout: int = 300
    
    # Web Search Configuration (Tavily)
    tavily_api_key: str = ""
    
    # FAISS Vector Store Configuration
    faiss_index_path: str = "./data/faiss_index"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Checkpoint & Session Configuration
    checkpoint_path: str = "./data/checkpoints"
    session_memory_type: str = "memory"  
    
    # Research Configuration
    max_sources_default: int = 10
    max_refinement_passes: int = 3
    chunk_size: int = 1000
    
    # Feature Flags
    enable_source_tracking: bool = True
    enable_streaming: bool = True
    debug_mode: bool = False
    
    # Ollama Retry Configuration
    max_retries: int = 3
    retry_wait_seconds: int = 1
    
    class Config:
        """Pydantic config for loading from .env file and environment variables."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def __init__(self, **data):
        """Initialize settings and create necessary directories."""
        super().__init__(**data)
        self._create_directories()
    
    def _create_directories(self) -> None:
        """Create required directories if they don't exist."""
        dirs_to_create = [
            Path(self.faiss_index_path).parent,
            Path(self.checkpoint_path),
        ]
        for directory in dirs_to_create:
            directory.mkdir(parents=True, exist_ok=True)
    
    @property
    def is_production(self) -> bool:
        """Determine if running in production mode."""
        return os.getenv("ENVIRONMENT", "development").lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Determine if running in development mode."""
        return not self.is_production
    
    def get_checkpoint_db_path(self) -> str:
        """Get full path to checkpoint SQLite database."""
        return os.path.join(self.checkpoint_path, "checkpoints.db")
    
    def get_faiss_index_path(self) -> str:
        """Get full path to FAISS index."""
        return os.path.join(self.faiss_index_path, "index")


# Global settings instance
settings = Settings()


# Validation: Ensure Ollama is reachable in production
if settings.is_production and settings.session_memory_type == "sqlite":
    if not os.path.exists(settings.checkpoint_path):
        raise ValueError(
            f"Checkpoint path does not exist: {settings.checkpoint_path}"
        )


__all__ = ["settings", "Settings"]

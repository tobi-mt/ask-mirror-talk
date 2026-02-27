from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore extra fields from .env
    )

    # Core
    app_name: str = "Ask Mirror Talk"
    environment: str = "dev"

    # Database
    database_url: str = "postgresql+psycopg://mirror:mirror@localhost:5432/mirror_talk"
    
    @field_validator("database_url")
    @classmethod
    def fix_database_url(cls, v: str) -> str:
        """
        Fix database URL for psycopg3 compatibility.
        
        We use psycopg3 (psycopg[binary]>=3.1.0), which requires the +psycopg dialect.
        
        Conversions:
        - postgres://...       → postgresql+psycopg://...
        - postgresql://...     → postgresql+psycopg://...  
        - postgresql+psycopg2://... → postgresql+psycopg://...
        - postgresql+psycopg://...  → postgresql+psycopg://... (no change)
        """
        import logging
        logger = logging.getLogger(__name__)
        
        original = v
        
        if v.startswith("postgres://"):
            #Render provides postgres://, convert to postgresql+psycopg://
            v = v.replace("postgres://", "postgresql+psycopg://", 1)
        elif v.startswith("postgresql+psycopg2://"):
            # Wrong dialect, we use psycopg3, not psycopg2
            v = v.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
        elif v.startswith("postgresql://") and "+psycopg" not in v:
            # Missing dialect, add +psycopg for psycopg3
            v = v.replace("postgresql://", "postgresql+psycopg://", 1)
        
        if original != v:
            logger.info(f"Database URL converted for psycopg3 compatibility")
            logger.info(f"  From: {original.split('@')[0].split('//')[0]}://***")
            logger.info(f"  To:   {v.split('@')[0].split('//')[0]}://***")
        
        return v

    # Storage
    data_dir: str = "data"
    audio_dir: str = "data/audio"
    transcript_dir: str = "data/transcripts"

    # RSS
    rss_url: str = ""
    rss_poll_minutes: int = 60

    # Ingestion
    max_episodes_per_run: int = 3

    # Chunking
    max_chunk_chars: int = 1400
    min_chunk_chars: int = 300

    # Retrieval
    top_k: int = 6
    min_similarity: float = 0.15
    diversity_lambda: float = 0.7  # MMR: 0.0=max diversity, 1.0=max relevance
    max_cited_episodes: int = 5  # Maximum number of episodes to cite in response

    # Embeddings
    embedding_provider: str = "local"  # local | sentence_transformers | openai
    embedding_dim: int = 384

    # Transcription
    transcription_provider: str = "openai"  # openai | faster_whisper | none
    whisper_model: str = "tiny"  # Only used if transcription_provider="faster_whisper"
    openai_api_key: str | None = None  # OpenAI API key for transcription (optional if using faster_whisper)

    # Answer Generation
    answer_generation_provider: str = "openai"  # openai | basic
    answer_generation_model: str = "gpt-4o-mini"  # gpt-4o-mini | gpt-4o | gpt-4-turbo
    answer_max_tokens: int = 800  # Maximum tokens for generated answers
    answer_temperature: float = 0.7  # 0.0 = deterministic, 1.0 = creative
    cache_similarity_threshold: float = 0.92  # Minimum cosine similarity for cache hits (0.0-1.0)
    cache_ttl_seconds: int = 14400  # Cache TTL (default: 4 hours)

    # API
    rate_limit_per_minute: int = 20
    allowed_origins: str = ""  # comma-separated origins for CORS

    # Admin dashboard
    admin_enabled: bool = True
    admin_user: str = "admin"
    admin_password: str = "change-me"
    admin_ip_allowlist: str = ""  # comma-separated CIDRs or IPs

    # Push Notifications (VAPID)
    vapid_public_key: str = ""  # Base64url-encoded public key for browser subscriptions
    vapid_private_key: str = ""  # PEM-encoded private key for signing push messages
    vapid_claim_email: str = ""  # Contact email for VAPID claims (e.g. mailto:you@example.com)

    @field_validator("vapid_private_key")
    @classmethod
    def fix_vapid_pem(cls, v: str) -> str:
        """Ensure literal \\n in PEM env vars become real newlines."""
        if v and "\\n" in v:
            v = v.replace("\\n", "\n")
        return v


settings = Settings()

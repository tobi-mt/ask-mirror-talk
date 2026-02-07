from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Core
    app_name: str = "Ask Mirror Talk"
    environment: str = "dev"

    # Database
    database_url: str = "postgresql+psycopg://mirror:mirror@localhost:5432/mirror_talk"

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

    # Embeddings
    embedding_provider: str = "local"  # local | sentence_transformers
    embedding_dim: int = 384

    # Transcription
    transcription_provider: str = "faster_whisper"  # faster_whisper | none
    whisper_model: str = "base"

    # API
    rate_limit_per_minute: int = 20

    # Admin dashboard
    admin_enabled: bool = True
    admin_user: str = "admin"
    admin_password: str = "change-me"
    admin_ip_allowlist: str = ""  # comma-separated CIDRs or IPs


settings = Settings()

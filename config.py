"""Configuration management for the application."""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # Database Configuration
    db_user: str = os.getenv("DB_USER", "")
    db_password: str = os.getenv("DB_PASSWORD", "")
    db_host: str = os.getenv("DB_HOST", "")
    db_port: int = int(os.getenv("DB_PORT", "31306"))
    db_name: str = os.getenv("DB_NAME", "eshtri")
    
    # RAG Configuration
    rag_db_path: str = os.getenv("RAG_DB_PATH", "./rag_db")
    # embedding_model: str = "text-embedding-3-small"
    # embedding_model: str = "intfloat/multilingual-e5-large"
    # 🚀 PERFORMANCE: Using smaller/faster model (3x faster than large)
    embedding_model: str = "intfloat/multilingual-e5-base"
    
    # LLM Configuration
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.2
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = "chat_log.txt"
    enable_file_logging: bool = False  # Disable per-request file logging for speed
    enable_debug_logging: bool = False  # Disable verbose debug prints for speed
    enable_rag_debug: bool = False  # Disable RAG debug output
    
    # Application
    app_title: str = "Eshtri Aqar Chatbot"
    app_version: str = "1.0.0"
    
    # Performance Optimization Flags
    enable_intent_classifier: bool = False  # Disabled for speed
    enable_cross_validation: bool = False  # Disabled for speed
    rag_chunk_count: int = 3  # Reduced further for speed
    preprocessing_min_words: int = 50  # Skip preprocessing for most queries
    max_chat_history_messages: int = 2  # Minimal context for speed
    use_llm_language_detection: bool = False  # Use heuristics only for speed
    enable_safety_guard: bool = False  # Skip safety guard LLM call for speed
    
    @property
    def db_config(self) -> dict:
        """Return database configuration as a dictionary."""
        return {
            "user": self.db_user,
            "password": self.db_password,
            "host": self.db_host,
            "port": self.db_port,
            "database": self.db_name
        }
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Database columns
COLUMNS = [
    "lang_id", "comp_text_id", "unt_code", "unit_id", "area", "balcony", "bathroom",
    "room", "floor", "garden_size", "stat_id", "price", "delivery_date", "phs_usg_id",
    "finishing", "comp_id", "developer_description_short", "developer_name", "reg_id",
    "region_text", "category", "cat_id", "usage_text", "model_text", "model_name",
    "mod_id", "sec_id", "compound_text", "compound_name", "usg_id", "dev_id", "dev_code",
    "comp_code", "mod_code", "kitchen", "storage", "utility", "bld_id", "outdoor_area", "terrace",
    "roof_area", "dressing", "club", "garage", "ac", "down_payment", "deposit", "monthly_installment",
    "installment_type", "payment_plan", "promo_text", "price_update_date", "flr_code", "three_d_url", "video_url",
    "flr_id", "sec_code", "has_promo", "comp_feature_1", "comp_feature_2", "comp_feature_3", "comp_feature_4", "sorting_id",
    "unit_image", "sm_unit_image", "unit_image2", "developer_logo", "sm_developer_logo", "md_developer_logo", "compound_image",
    "unit_search_status", "status_text", "financing"
]

DB_CONFIG = settings.db_config

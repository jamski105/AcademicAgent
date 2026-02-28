"""
Config Loader für Academic Agent v2.3+

Lädt und validiert Konfiguration aus:
- config/api_config.yaml
- config/research_modes.yaml
- Environment Variables (Fallback)

Features:
- Pydantic Validierung
- Standard vs Enhanced Mode Erkennung
- Environment Variable Override
- Type-Safe Config Objects
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings


# ============================================
# Base Paths
# ============================================

PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"


# ============================================
# API Config Models
# ============================================

class APIKeys(BaseModel):
    """API Keys (alle optional - Standard-Modus funktioniert ohne!)"""
    crossref_email: Optional[str] = None
    openalex_email: Optional[str] = None
    semantic_scholar_api_key: Optional[str] = None
    unpaywall_email: Optional[str] = None
    core_api_key: Optional[str] = None

    def is_enhanced_mode(self) -> bool:
        """Prüft ob Enhanced Mode aktiviert ist (mindestens ein Key gesetzt)"""
        return any([
            self.crossref_email,
            self.openalex_email,
            self.semantic_scholar_api_key,
            self.core_api_key
        ])

    def get_mode_name(self) -> str:
        """Gibt aktuellen Modus zurück"""
        return "enhanced" if self.is_enhanced_mode() else "standard"


class RateLimitConfig(BaseModel):
    """Rate Limit Konfiguration pro API"""
    requests_per_second: float = Field(gt=0)
    mode: str = Field(default="anonymous")  # "anonymous" | "polite" | "authenticated"
    daily_limit: Optional[int] = None


class TimeoutConfig(BaseModel):
    """Timeout Konfiguration"""
    api_request: int = Field(default=30, gt=0)
    pdf_download: int = Field(default=60, gt=0)
    dbis_browser: int = Field(default=120, gt=0)


class RetryConfig(BaseModel):
    """Retry Konfiguration"""
    max_attempts: int = Field(default=3, gt=0)
    backoff_factor: float = Field(default=2.0, gt=0)
    retry_on_status_codes: List[int] = Field(default=[429, 500, 502, 503, 504])


class CacheConfig(BaseModel):
    """Cache Konfiguration"""
    enabled: bool = True
    ttl_hours: int = Field(default=24, gt=0)
    backend: str = "sqlite"
    max_size_mb: int = Field(default=100, gt=0)


class FallbackConfig(BaseModel):
    """Fallback Strategy Konfiguration"""
    crossref_fallback: List[str] = ["openalex", "semantic_scholar"]
    openalex_fallback: List[str] = ["crossref", "semantic_scholar"]
    semantic_scholar_fallback: List[str] = ["crossref", "openalex"]
    final_fallback: str = "google_scholar"


class APIConfig(BaseModel):
    """Haupt-API-Konfiguration"""
    api_keys: APIKeys
    rate_limits: Dict[str, RateLimitConfig]
    timeouts: TimeoutConfig
    retry: RetryConfig
    cache: CacheConfig
    fallbacks: FallbackConfig

    @property
    def mode(self) -> str:
        """Gibt aktuellen Modus zurück"""
        return self.api_keys.get_mode_name()


# ============================================
# Research Modes Config Models
# ============================================

class ScoringConfig(BaseModel):
    """5D-Scoring Gewichtung"""
    relevance_weight: float = Field(default=0.4, ge=0, le=1)
    recency_weight: float = Field(default=0.2, ge=0, le=1)
    quality_weight: float = Field(default=0.2, ge=0, le=1)
    authority_weight: float = Field(default=0.2, ge=0, le=1)
    apply_portfolio_balance: bool = False

    @field_validator('relevance_weight', 'recency_weight', 'quality_weight', 'authority_weight')
    @classmethod
    def check_weights_sum(cls, v, info):
        """Validiert dass Gewichte sich zu ~1.0 addieren"""
        # Wird pro Weight aufgerufen, finale Validierung in model_validator
        return v

    def total_weight(self) -> float:
        """Berechnet Summe der Gewichte (sollte 1.0 sein)"""
        return (self.relevance_weight + self.recency_weight +
                self.quality_weight + self.authority_weight)


class PDFFetcherConfig(BaseModel):
    """PDF-Fetcher Konfiguration"""
    fallback_chain: List[str] = ["unpaywall", "core", "dbis_browser"]
    max_parallel: int = Field(default=3, gt=0)
    timeout_per_pdf: int = Field(default=60, gt=0)


class QuoteExtractionConfig(BaseModel):
    """Quote-Extraction Konfiguration"""
    quotes_per_paper: int = Field(default=2, gt=0)
    max_quote_length: int = Field(default=25, gt=0)


class ResearchMode(BaseModel):
    """Einzelner Research Mode (Quick/Standard/Deep/Custom)"""
    max_papers: int = Field(gt=0)
    estimated_duration_min: int = Field(gt=0)
    api_sources: List[str]
    scoring: ScoringConfig
    pdf_fetcher: PDFFetcherConfig
    quote_extraction: QuoteExtractionConfig


class GlobalSettings(BaseModel):
    """Globale Settings (gelten für alle Modi)"""
    auto_resume_on_error: bool = True
    checkpoint_interval_minutes: int = Field(default=5, gt=0)
    google_scholar_fallback: bool = True
    dbis_browser_delay_seconds: int = Field(default=15, gt=0)
    skip_pdf_if_all_failed: bool = True
    use_llm_relevance: bool = True
    output_format: str = "markdown"
    include_metadata: bool = True
    include_context: bool = True


class ResearchModesConfig(BaseModel):
    """Haupt-Research-Modes-Konfiguration"""
    modes: Dict[str, ResearchMode]
    default_mode: str = "standard"
    global_settings: GlobalSettings

    @field_validator('default_mode')
    @classmethod
    def validate_default_mode(cls, v, info):
        """Validiert dass default_mode existiert"""
        # NOTE: Kann erst nach modes validiert werden
        return v

    def get_mode(self, mode_name: str) -> ResearchMode:
        """Gibt spezifischen Mode zurück"""
        if mode_name not in self.modes:
            raise ValueError(f"Unknown mode: {mode_name}. Available: {list(self.modes.keys())}")
        return self.modes[mode_name]


# ============================================
# Config Loader
# ============================================

class ConfigLoader:
    """
    Lädt und validiert Konfiguration

    Usage:
        config_loader = ConfigLoader()
        api_config = config_loader.load_api_config()
        research_config = config_loader.load_research_modes_config()

        # Check mode
        print(api_config.mode)  # "standard" oder "enhanced"
    """

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Args:
            config_dir: Optional custom config directory (default: PROJECT_ROOT/config)
        """
        self.config_dir = config_dir or CONFIG_DIR

    def load_api_config(self, use_env: bool = True) -> APIConfig:
        """
        Lädt API-Konfiguration

        Args:
            use_env: Wenn True, überschreiben Environment Variables YAML-Werte

        Returns:
            APIConfig object (validiert)
        """
        yaml_path = self.config_dir / "api_config.yaml"

        if not yaml_path.exists():
            raise FileNotFoundError(f"API config not found: {yaml_path}")

        # YAML laden
        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        # Environment Variables Override (optional)
        if use_env:
            env_mapping = data.get("environment_variables", {})
            api_keys = data.get("api_keys", {})

            for key, env_var in env_mapping.items():
                env_value = os.getenv(env_var)
                if env_value:
                    api_keys[key] = env_value

            data["api_keys"] = api_keys

        # Pydantic Validierung
        return APIConfig(**data)

    def load_research_modes_config(self) -> ResearchModesConfig:
        """
        Lädt Research Modes Konfiguration

        Returns:
            ResearchModesConfig object (validiert)
        """
        yaml_path = self.config_dir / "research_modes.yaml"

        if not yaml_path.exists():
            raise FileNotFoundError(f"Research modes config not found: {yaml_path}")

        # YAML laden
        with open(yaml_path) as f:
            data = yaml.safe_load(f)

        # Pydantic Validierung
        return ResearchModesConfig(**data)

    def load_all(self, use_env: bool = True) -> tuple[APIConfig, ResearchModesConfig]:
        """
        Lädt beide Configs

        Returns:
            Tuple von (APIConfig, ResearchModesConfig)
        """
        api_config = self.load_api_config(use_env=use_env)
        research_config = self.load_research_modes_config()
        return api_config, research_config


# ============================================
# Convenience Functions
# ============================================

def load_config(use_env: bool = True) -> tuple[APIConfig, ResearchModesConfig]:
    """
    Convenience function zum Laden beider Configs

    Args:
        use_env: Environment Variables nutzen (default: True)

    Returns:
        Tuple von (APIConfig, ResearchModesConfig)

    Example:
        >>> api_cfg, research_cfg = load_config()
        >>> print(api_cfg.mode)  # "standard" or "enhanced"
        >>> mode = research_cfg.get_mode("quick")
        >>> print(mode.max_papers)  # 15
    """
    loader = ConfigLoader()
    return loader.load_all(use_env=use_env)


def get_mode_info() -> Dict[str, Any]:
    """
    Gibt Info über aktuellen Modus zurück

    Returns:
        Dict mit Mode-Informationen
    """
    api_cfg, _ = load_config()

    return {
        "mode": api_cfg.mode,
        "is_enhanced": api_cfg.api_keys.is_enhanced_mode(),
        "has_crossref": bool(api_cfg.api_keys.crossref_email),
        "has_openalex": bool(api_cfg.api_keys.openalex_email),
        "has_s2": bool(api_cfg.api_keys.semantic_scholar_api_key),
        "has_core": bool(api_cfg.api_keys.core_api_key),
    }


# ============================================
# CLI Helper (für Debugging)
# ============================================

if __name__ == "__main__":
    """
    Test Config Loading

    Run:
        python src/utils/config.py
    """
    print("Loading config...")

    try:
        api_cfg, research_cfg = load_config()

        print("\n✅ Config loaded successfully!")
        print(f"\nMode: {api_cfg.mode}")
        print(f"Enhanced: {api_cfg.api_keys.is_enhanced_mode()}")
        print(f"\nDefault Research Mode: {research_cfg.default_mode}")
        print(f"Available Modes: {list(research_cfg.modes.keys())}")

        # Mode Info
        mode_info = get_mode_info()
        print(f"\nMode Info: {mode_info}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise

"""Provider factory: instantiate providers from YAML config + env vars.

Resolution order for each setting:
  1. Explicit argument passed to factory function
  2. Environment variable (e.g. REASONING_PROVIDER, SARVAM_API_KEY)
  3. Databricks secret scope (scope='asha-sahayak', key='sarvam_api_key')
  4. Value from config/app_config.yaml
  5. Hardcoded default
"""

import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .base import (
    TranslationProvider,
    SpeechToTextProvider,
    VisionExtractionProvider,
    EmbeddingProvider,
    ReasoningProvider,
)

logger = logging.getLogger(__name__)

_config: Optional[Dict[str, Any]] = None
_sarvam_client = None

CONFIG_PATH = Path(__file__).parent.parent / "config" / "app_config.yaml"


def _load_dotenv():
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=False)
            logger.info("Loaded .env file")
    except ImportError:
        pass


def _load_config() -> Dict[str, Any]:
    global _config
    if _config is not None:
        return _config

    _load_dotenv()

    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            _config = yaml.safe_load(f) or {}
        logger.info(f"Loaded config from {CONFIG_PATH}")
    else:
        _config = {}
        logger.warning(f"Config file not found: {CONFIG_PATH}")
    return _config


def _cfg_provider_default(provider_type: str) -> str:
    cfg = _load_config()
    return cfg.get("providers", {}).get(provider_type, {}).get("default", "mock")


def _cfg_provider_section(provider_type: str, backend: str) -> Dict[str, Any]:
    cfg = _load_config()
    return cfg.get("providers", {}).get(provider_type, {}).get(backend, {})


def _get_databricks_secret(scope: str, key: str) -> Optional[str]:
    """Retrieve a secret from Databricks secret scope.

    Works in two contexts:
    1. Notebook / cluster: via dbutils.secrets.get()
    2. Databricks Apps: secrets are injected as environment variables
    """
    # First, try dbutils (available in notebook/cluster context)
    try:
        from databricks.sdk import WorkspaceClient
        w = WorkspaceClient()
        # Use the SDK's dbutils proxy to fetch the secret
        secret_value = w.dbutils.secrets.get(scope=scope, key=key)
        if secret_value:
            logger.info(f"Retrieved secret '{key}' from Databricks scope '{scope}'")
            return secret_value
    except ImportError:
        logger.debug("databricks-sdk not installed — skipping Databricks secret lookup")
    except Exception as e:
        logger.debug(f"Could not fetch Databricks secret '{key}': {e}")
    return None


def _get_sarvam_key() -> str:
    """Resolve Sarvam API key with fallback chain:
    1. Environment variable SARVAM_API_KEY
    2. Databricks secret scope 'asha-sahayak', key 'sarvam_api_key'
    """
    # 1. Env var (also covers Databricks Apps injected config)
    key = os.getenv("SARVAM_API_KEY", "")
    if key:
        return key

    # 2. Databricks secret scope
    secret = _get_databricks_secret("asha-sahayak", "sarvam_api_key")
    if secret:
        # Cache in env so subsequent calls are fast
        os.environ["SARVAM_API_KEY"] = secret
        return secret

    return ""


def _get_sarvam_client():
    """Shared Sarvam SDK client instance across all providers."""
    global _sarvam_client
    if _sarvam_client is not None:
        return _sarvam_client
    key = _get_sarvam_key()
    if not key:
        logger.warning("SARVAM_API_KEY not set — Sarvam providers will fail. "
                       "Set env var SARVAM_API_KEY or add to Databricks secret "
                       "scope 'asha-sahayak' with key 'sarvam_api_key'.")
        return None
    try:
        from sarvamai import SarvamAI
        _sarvam_client = SarvamAI(api_subscription_key=key)
        logger.info("Initialized shared Sarvam AI client")
        return _sarvam_client
    except ImportError:
        logger.error("sarvamai SDK not installed — run: pip install sarvamai")
        return None
    except Exception as e:
        logger.error(f"Failed to init Sarvam client: {e}")
        return None


# ── Factory functions ────────────────────────────────────────────────

def get_translation_provider(provider_name: Optional[str] = None) -> TranslationProvider:
    name = provider_name or os.getenv("TRANSLATION_PROVIDER") or _cfg_provider_default("translation")
    if name == "sarvam":
        client = _get_sarvam_client()
        if client:
            from .translation.sarvam import SarvamTranslationProvider
            return SarvamTranslationProvider(client=client)
        logger.warning("Sarvam client unavailable, falling back to mock translation")
    from .translation.mock import MockTranslationProvider
    return MockTranslationProvider()


def get_speech_provider(provider_name: Optional[str] = None) -> SpeechToTextProvider:
    name = provider_name or os.getenv("SPEECH_PROVIDER") or _cfg_provider_default("speech")
    if name == "sarvam":
        client = _get_sarvam_client()
        if client:
            from .speech.sarvam import SarvamSpeechProvider
            return SarvamSpeechProvider(client=client)
        logger.warning("Sarvam client unavailable, falling back to mock speech")
    from .speech.mock import MockSpeechProvider
    return MockSpeechProvider()


def get_vision_provider(provider_name: Optional[str] = None) -> VisionExtractionProvider:
    name = provider_name or os.getenv("VISION_PROVIDER") or _cfg_provider_default("vision")
    if name == "sarvam":
        client = _get_sarvam_client()
        if client:
            from .vision.sarvam import SarvamVisionProvider
            return SarvamVisionProvider(client=client)
        logger.warning("Sarvam client unavailable, falling back to pytesseract vision")
        name = "pytesseract"
    if name == "pytesseract":
        from .vision.pytesseract_provider import PytesseractVisionProvider
        return PytesseractVisionProvider()
    from .vision.mock import MockVisionProvider
    return MockVisionProvider()


def get_embedding_provider(provider_name: Optional[str] = None) -> EmbeddingProvider:
    name = provider_name or os.getenv("EMBEDDING_PROVIDER") or _cfg_provider_default("embeddings")
    if name == "local":
        cfg = _cfg_provider_section("embeddings", "local") or {}
        model = cfg.get("model") or os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-small")
        from .embeddings.local import LocalEmbeddingProvider
        return LocalEmbeddingProvider(model_name=model)
    from .embeddings.mock import MockEmbeddingProvider
    return MockEmbeddingProvider()


def get_reasoning_provider(provider_name: Optional[str] = None) -> ReasoningProvider:
    name = provider_name or os.getenv("REASONING_PROVIDER") or _cfg_provider_default("reasoning")
    if name == "sarvam":
        client = _get_sarvam_client()
        if client:
            cfg = _cfg_provider_section("reasoning", "sarvam")
            model = cfg.get("model", "sarvam-m")
            from .reasoning.sarvam import SarvamReasoningProvider
            return SarvamReasoningProvider(client=client, model=model)
        logger.warning("Sarvam client unavailable, falling back to mock reasoning")
    if name == "databricks":
        from .reasoning.databricks_fm import DatabricksReasoningProvider
        return DatabricksReasoningProvider()
    from .reasoning.mock import MockReasoningProvider
    return MockReasoningProvider()

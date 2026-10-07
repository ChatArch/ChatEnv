"""ChatArch typed environment profile manager."""

from .fields import BaseEnvConfig, EnvField
from .paths import ChatArchPaths, get_paths
from .store import EnvStore
from .token_refreshers import TokenRefreshResult
from .tokens import TokenStore
from .configs import ChatArchConfig, FeishuConfig, OpenAIConfig
from .discovery import get_provider_configs, get_provider_errors, load_config_providers
from .policy import (
    AUTO_PROMPT_DEFAULT,
    AUTO_PROMPT_ENV_VAR,
    auto_prompt_enabled,
    auto_prompt_value_enabled,
    resolve_auto_prompt_enabled,
    resolve_auto_prompt_value,
)

__all__ = [
    "BaseEnvConfig",
    "ChatArchConfig",
    "ChatArchPaths",
    "EnvField",
    "EnvStore",
    "FeishuConfig",
    "OpenAIConfig",
    "TokenRefreshResult",
    "TokenStore",
    "AUTO_PROMPT_DEFAULT",
    "AUTO_PROMPT_ENV_VAR",
    "auto_prompt_enabled",
    "auto_prompt_value_enabled",
    "get_provider_configs",
    "get_provider_errors",
    "get_paths",
    "load_config_providers",
    "resolve_auto_prompt_enabled",
    "resolve_auto_prompt_value",
    "__version__",
]

__version__ = "0.2.11"

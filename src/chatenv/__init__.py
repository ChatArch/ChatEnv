"""ChatArch typed environment profile manager."""

from .fields import BaseEnvConfig, EnvField
from .paths import ChatArchPaths, get_paths
from .store import EnvStore
from .configs import FeishuConfig, OpenAIConfig
from .discovery import get_provider_configs, get_provider_errors, load_config_providers

__all__ = [
    "BaseEnvConfig",
    "ChatArchPaths",
    "EnvField",
    "EnvStore",
    "FeishuConfig",
    "OpenAIConfig",
    "get_provider_configs",
    "get_provider_errors",
    "get_paths",
    "load_config_providers",
    "__version__",
]

__version__ = "0.2.0"

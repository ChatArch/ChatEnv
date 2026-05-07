"""ChatArch typed environment profile manager."""

from .fields import BaseEnvConfig, EnvField
from .paths import ChatArchPaths, get_paths
from .store import EnvStore

__all__ = [
    "BaseEnvConfig",
    "ChatArchPaths",
    "EnvField",
    "EnvStore",
    "get_paths",
    "__version__",
]

__version__ = "0.1.0"

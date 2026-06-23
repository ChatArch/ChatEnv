"""Built-in shared ChatArch env schemas.

Only broadly shared configuration schemas live here. Package-specific schemas
should stay in their owning package and register through ``chatenv.configs``
entry points.
"""

from __future__ import annotations

from .fields import BaseEnvConfig, EnvField


class OpenAIConfig(BaseEnvConfig):
    """Shared OpenAI-compatible model provider configuration."""

    _title = "OpenAI Configuration"
    _aliases = ["oai", "openai"]
    _storage_dir = "OpenAI"
    _order = 10

    OPENAI_API_BASE = EnvField(
        "OPENAI_API_BASE",
        desc="The base URL of the API, usually with suffix /v1.",
    )
    OPENAI_API_KEY = EnvField(
        "OPENAI_API_KEY",
        desc="OpenAI-compatible API key",
        is_sensitive=True,
    )
    OPENAI_API_MODEL = EnvField(
        "OPENAI_API_MODEL",
        default="gpt-5.5",
        desc="Default model name",
    )
    OPENAI_ACCESS_TOKEN = EnvField(
        "OPENAI_ACCESS_TOKEN",
        desc="OpenAI OAuth access token for OAuth-backed capabilities.",
        is_sensitive=True,
    )
    OPENAI_REFRESH_TOKEN = EnvField(
        "OPENAI_REFRESH_TOKEN",
        desc="OpenAI OAuth refresh token for OAuth-backed capabilities.",
        is_sensitive=True,
    )
    OPENAI_OAUTH_BASE_URL = EnvField(
        "OPENAI_OAUTH_BASE_URL",
        default="https://auth.openai.com",
        desc="OpenAI OAuth auth server base URL used to refresh access tokens.",
    )
    OPENAI_ACCESS_TOKEN_EXPIRES_AT = EnvField(
        "OPENAI_ACCESS_TOKEN_EXPIRES_AT",
        desc="UTC ISO timestamp when the OpenAI OAuth access token expires.",
    )
    OPENAI_IMAGE_MODEL = EnvField(
        "OPENAI_IMAGE_MODEL",
        default="gpt-image-2-medium",
        desc="Default OpenAI image model preset.",
    )


class FeishuConfig(BaseEnvConfig):
    """Shared Feishu/Lark app and bot configuration."""

    _title = "Feishu Configuration"
    _aliases = ["feishu", "lark"]
    _storage_dir = "Feishu"
    _order = 20

    FEISHU_APP_ID = EnvField(
        "FEISHU_APP_ID",
        desc="Feishu/Lark app ID from the developer console.",
    )
    FEISHU_APP_SECRET = EnvField(
        "FEISHU_APP_SECRET",
        desc="Feishu/Lark app secret.",
        is_sensitive=True,
    )
    FEISHU_API_BASE = EnvField(
        "FEISHU_API_BASE",
        default="https://open.feishu.cn",
        desc="Feishu/Lark API base URL. Use https://open.larksuite.com for Lark.",
    )
    FEISHU_DEFAULT_RECEIVER_ID = EnvField(
        "FEISHU_DEFAULT_RECEIVER_ID",
        desc="Default user receive_id for Feishu/Lark sends.",
    )
    FEISHU_DEFAULT_CHAT_ID = EnvField(
        "FEISHU_DEFAULT_CHAT_ID",
        desc="Default chat_id for Feishu/Lark chat sends.",
    )
    FEISHU_ENCRYPT_KEY = EnvField(
        "FEISHU_ENCRYPT_KEY",
        desc="Feishu/Lark event encrypt key.",
        is_sensitive=True,
    )
    FEISHU_VERIFY_TOKEN = EnvField(
        "FEISHU_VERIFY_TOKEN",
        desc="Feishu/Lark event verification token.",
        is_sensitive=True,
    )


__all__ = ["OpenAIConfig", "FeishuConfig"]

from __future__ import annotations

from chatenv.fields import BaseEnvConfig, EnvField


class OpenAIConfig(BaseEnvConfig):
    _title = "OpenAI Configuration"
    _aliases = ["oai", "openai"]
    _storage_dir = "OpenAI"

    OPENAI_API_BASE = EnvField("OPENAI_API_BASE", desc="The base url of the API (with suffix /v1).")
    OPENAI_API_KEY = EnvField("OPENAI_API_KEY", desc="Your API key", is_sensitive=True)
    OPENAI_API_MODEL = EnvField("OPENAI_API_MODEL", default="gpt-3.5-turbo", desc="The default model name")


class CRSConfig(BaseEnvConfig):
    _title = "Claude Relay Service Configuration"
    _aliases = ["crs", "claude-relay"]
    _storage_dir = "CRS"

    CRS_API_BASE = EnvField("CRS_API_BASE", desc="Claude Relay Service root URL.")
    CRS_API_KEY = EnvField("CRS_API_KEY", desc="CRS downstream API key.", is_sensitive=True)
    CRS_USERNAME = EnvField("CRS_USERNAME", desc="CRS admin username.")
    CRS_PASSWORD = EnvField("CRS_PASSWORD", desc="CRS admin password.", is_sensitive=True)
    CRS_ACCESS_TOKEN = EnvField("CRS_ACCESS_TOKEN", desc="CRS admin session token.", is_sensitive=True)


class SkillsConfig(BaseEnvConfig):
    _title = "ChatTool Skills Configuration"
    _aliases = ["skills", "skill", "chattool-skills"]
    _storage_dir = "Skills"

    CHATTOOL_SKILLS_DIR = EnvField("CHATTOOL_SKILLS_DIR", desc="Default ChatTool skills source directory.")


class AzureConfig(BaseEnvConfig):
    _title = "Azure OpenAI Configuration"
    _aliases = ["azure", "az"]
    _storage_dir = "Azure"

    AZURE_OPENAI_API_KEY = EnvField("AZURE_OPENAI_API_KEY", desc="Azure OpenAI API Key", is_sensitive=True)
    AZURE_OPENAI_ENDPOINT = EnvField("AZURE_OPENAI_ENDPOINT", desc="Azure OpenAI Endpoint")
    AZURE_OPENAI_API_VERSION = EnvField("AZURE_OPENAI_API_VERSION", desc="Azure OpenAI API Version")
    AZURE_OPENAI_API_MODEL = EnvField("AZURE_OPENAI_API_MODEL", desc="Azure OpenAI Deployment Name")


class AliyunConfig(BaseEnvConfig):
    _title = "Alibaba Cloud (Aliyun) Configuration"
    _aliases = ["ali", "aliyun", "alidns"]
    _storage_dir = "Aliyun"

    ALIBABA_CLOUD_ACCESS_KEY_ID = EnvField("ALIBABA_CLOUD_ACCESS_KEY_ID", desc="Access Key ID", is_sensitive=True)
    ALIBABA_CLOUD_ACCESS_KEY_SECRET = EnvField("ALIBABA_CLOUD_ACCESS_KEY_SECRET", desc="Access Key Secret", is_sensitive=True)
    ALIBABA_CLOUD_REGION_ID = EnvField("ALIBABA_CLOUD_REGION_ID", default="cn-hangzhou", desc="Region ID")


class TencentConfig(BaseEnvConfig):
    _title = "Tencent Cloud Configuration"
    _aliases = ["tencent", "tx", "tencent-dns"]
    _storage_dir = "Tencent"

    TENCENT_SECRET_ID = EnvField("TENCENT_SECRET_ID", desc="Secret ID", is_sensitive=True)
    TENCENT_SECRET_KEY = EnvField("TENCENT_SECRET_KEY", desc="Secret Key", is_sensitive=True)
    TENCENT_REGION_ID = EnvField("TENCENT_REGION_ID", default="ap-guangzhou", desc="Region ID")


class ZulipConfig(BaseEnvConfig):
    _title = "Zulip Configuration"
    _aliases = ["zulip"]
    _storage_dir = "Zulip"

    ZULIP_BOT_EMAIL = EnvField("ZULIP_BOT_EMAIL", desc="Zulip Bot Email")
    ZULIP_BOT_API_KEY = EnvField("ZULIP_BOT_API_KEY", desc="Zulip Bot API Key", is_sensitive=True)
    ZULIP_SITE = EnvField("ZULIP_SITE", desc="Zulip Site URL")
    ZULIP_NEWS_STREAMS = EnvField("ZULIP_NEWS_STREAMS", desc="Comma-separated stream names")
    ZULIP_NEWS_TOPICS = EnvField("ZULIP_NEWS_TOPICS", desc="Comma-separated topic names")
    ZULIP_NEWS_SINCE_HOURS = EnvField("ZULIP_NEWS_SINCE_HOURS", default="24", desc="Default hours for news window")
    ZULIP_NEWS_PER_STREAM = EnvField("ZULIP_NEWS_PER_STREAM", default="200", desc="Default per-stream fetch limit")


class FeishuConfig(BaseEnvConfig):
    _title = "Feishu Configuration"
    _aliases = ["feishu", "lark"]
    _storage_dir = "Feishu"

    FEISHU_APP_ID = EnvField("FEISHU_APP_ID", desc="Feishu App ID")
    FEISHU_APP_SECRET = EnvField("FEISHU_APP_SECRET", desc="Feishu App Secret", is_sensitive=True)
    FEISHU_API_BASE = EnvField("FEISHU_API_BASE", default="https://open.feishu.cn", desc="Feishu API Base URL")
    FEISHU_DEFAULT_RECEIVER_ID = EnvField("FEISHU_DEFAULT_RECEIVER_ID", desc="Default receive_id")
    FEISHU_DEFAULT_CHAT_ID = EnvField("FEISHU_DEFAULT_CHAT_ID", desc="Default chat_id")
    FEISHU_ENCRYPT_KEY = EnvField("FEISHU_ENCRYPT_KEY", desc="Feishu Encrypt Key")
    FEISHU_VERIFY_TOKEN = EnvField("FEISHU_VERIFY_TOKEN", desc="Feishu Verify Token")


class TongyiConfig(BaseEnvConfig):
    _title = "Tongyi Wanxiang Configuration"
    _aliases = ["tongyi", "dashscope"]
    _storage_dir = "Tongyi"

    DASHSCOPE_API_KEY = EnvField("DASHSCOPE_API_KEY", desc="Aliyun DashScope API Key", is_sensitive=True)


class HuggingFaceConfig(BaseEnvConfig):
    _title = "Hugging Face Configuration"
    _aliases = ["hf", "huggingface"]
    _storage_dir = "HuggingFace"

    HUGGINGFACE_HUB_TOKEN = EnvField("HUGGINGFACE_HUB_TOKEN", desc="Hugging Face User Access Token", is_sensitive=True)


class PollinationsConfig(BaseEnvConfig):
    _title = "Pollinations Configuration"
    _aliases = ["pollinations", "poll"]
    _storage_dir = "Pollinations"

    POLLINATIONS_API_KEY = EnvField("POLLINATIONS_API_KEY", desc="Pollinations API Key", is_sensitive=True)
    POLLINATIONS_MODEL_ID = EnvField("POLLINATIONS_MODEL_ID", default="flux", desc="Default Pollinations model ID")


class LiblibConfig(BaseEnvConfig):
    _title = "LiblibAI Configuration"
    _aliases = ["liblib"]
    _storage_dir = "Liblib"

    LIBLIB_MODEL_ID = EnvField("LIBLIB_MODEL_ID", desc="LiblibAI Model ID")
    LIBLIB_ACCESS_KEY = EnvField("LIBLIB_ACCESS_KEY", desc="LiblibAI Access Key", is_sensitive=True)
    LIBLIB_SECRET_KEY = EnvField("LIBLIB_SECRET_KEY", desc="LiblibAI Secret Key", is_sensitive=True)


class SiliconFlowConfig(BaseEnvConfig):
    _title = "SiliconFlow Configuration"
    _aliases = ["siliconflow"]
    _storage_dir = "SiliconFlow"

    SILICONFLOW_API_KEY = EnvField("SILICONFLOW_API_KEY", desc="SiliconFlow API Key", is_sensitive=True)
    SILICONFLOW_MODEL_ID = EnvField("SILICONFLOW_MODEL_ID", default="black-forest-labs/FLUX.1-schnell", desc="Default Image Model ID")


class TPLinkConfig(BaseEnvConfig):
    _title = "TP-Link Router Configuration"
    _aliases = ["tplink", "tplogin"]
    _storage_dir = "TPLink"

    TPLOGIN_URL = EnvField("TPLOGIN_URL", default="http://192.168.1.1", desc="TP-Link Router Login URL")
    TPLOGIN_AUTH_PASSWORD = EnvField("TPLOGIN_AUTH_PASSWORD", desc="TP-Link Router Password", is_sensitive=True)

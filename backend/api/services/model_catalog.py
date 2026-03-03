"""Model catalog module - contains built-in provider and model configurations.

This module is intentionally kept dependency-light:
it only imports APIKeyProvider enum, no service layer modules,
to avoid circular imports.
"""
from api.models.shared_api_key import APIKeyProvider

# Built-in provider information - single source of truth for hardcoded providers.
# variable name: BUILTIN_PROVIDER_INFO
# shared_api_key_service imports this as PROVIDER_INFO for backward compatibility.
BUILTIN_PROVIDER_INFO = {
    APIKeyProvider.BIGMODEL: {
        "name": "智谱 AI Coding Plan",
        "website": "https://bigmodel.cn",
        "supported_models": ["glm-5", "glm-4.7", "glm-4.6", "glm-4.5-air"],
        "logo_path": "/providers/bigmodel-logo.png",
        "models": {
            "glm-5": {
                "display_name": "GLM-5",
                "description": "智谱 AI 最新一代旗舰模型，超长上下文支持",
                "context_length": "200k",
                "max_output_length": "4k",
                "input_types": ["Text"],
                "output_types": ["Text"],
                "coding_score": None
            },
            "glm-4.7": {
                "display_name": "GLM-4.7",
                "description": "智谱 AI 最新一代旗舰模型，具备强大的理解和生成能力",
                "context_length": "128k",
                "max_output_length": "4k",
                "input_types": ["Text"],
                "output_types": ["Text"],
                "coding_score": 1441
            },
            "glm-4.6": {
                "display_name": "GLM-4.6",
                "description": "智谱 AI 高性能模型，平衡速度与质量",
                "context_length": "128k",
                "max_output_length": "4k",
                "input_types": ["Text"],
                "output_types": ["Text"],
                "coding_score": 1356
            },
            "glm-4.5-air": {
                "display_name": "GLM-4.5 Air",
                "description": "智谱 AI 轻量级模型，快速响应适合简单任务",
                "context_length": "128k",
                "max_output_length": "4k",
                "input_types": ["Text"],
                "output_types": ["Text"],
                "coding_score": None
            }
        }
    },
    APIKeyProvider.ZAI: {
        "name": "Z.AI Coding Plan",
        "website": "https://z.ai",
        "supported_models": ["glm-5", "glm-4.7", "glm-4.6", "glm-4.5-air"],
        "logo_path": "/providers/zai-logo.png",
        "models": {
            "glm-5": {
                "display_name": "GLM-5",
                "description": "智谱 AI 最新一代旗舰模型，超长上下文支持",
                "context_length": "200k",
                "max_output_length": "4k",
                "input_types": ["Text"],
                "output_types": ["Text"],
                "coding_score": None
            },
            "glm-4.7": {
                "display_name": "GLM-4.7",
                "description": "智谱 AI 最新一代旗舰模型，具备强大的理解和生成能力",
                "context_length": "128k",
                "max_output_length": "4k",
                "input_types": ["Text"],
                "output_types": ["Text"],
                "coding_score": 1441
            },
            "glm-4.6": {
                "display_name": "GLM-4.6",
                "description": "智谱 AI 高性能模型，平衡速度与质量",
                "context_length": "128k",
                "max_output_length": "4k",
                "input_types": ["Text"],
                "output_types": ["Text"],
                "coding_score": 1356
            },
            "glm-4.5-air": {
                "display_name": "GLM-4.5 Air",
                "description": "智谱 AI 轻量级模型，快速响应适合简单任务",
                "context_length": "128k",
                "max_output_length": "4k",
                "input_types": ["Text"],
                "output_types": ["Text"],
                "coding_score": None
            }
        }
    },
    APIKeyProvider.VOLCENGINE: {
        "name": "火山引擎 Coding Plan",
        "website": "https://volcengine.com",
        "supported_models": ["doubao-seed-code", "kimi-k2.5", "kimi-k2", "glm-4.7", "deepseek-v3.2"],
        "logo_path": "/providers/volcengine-logo.png",
        "models": {
            "doubao-seed-code": {
                "display_name": "Doubao Seed Code",
                "description": "豆包种子代码模型，专注于代码生成和理解",
                "context_length": "256k",
                "max_output_length": "32k",
                "input_types": ["Text", "Image"],
                "output_types": ["Text"],
                "coding_score": 1014
            },
            "kimi-k2.5": {
                "display_name": "Kimi K2.5",
                "description": "Kimi K2.5 高性能模型",
                "context_length": "128k",
                "max_output_length": "128k",
                "input_types": ["Text", "Image", "Video"],
                "output_types": ["Text"],
                "coding_score": 1447
            },
            "kimi-k2": {
                "display_name": "Kimi K2",
                "description": "Kimi K2 模型",
                "context_length": "128k",
                "max_output_length": "128k",
                "input_types": ["Text", "Image", "Video"],
                "output_types": ["Text"],
                "coding_score": 1330
            },
            "glm-4.7": {
                "display_name": "GLM-4.7",
                "description": "智谱 AI 最新一代旗舰模型，具备强大的理解和生成能力",
                "context_length": "128k",
                "max_output_length": "4k",
                "input_types": ["Text"],
                "output_types": ["Text"],
                "coding_score": 1441
            },
            "deepseek-v3.2": {
                "display_name": "DeepSeek V3.2",
                "description": "DeepSeek V3.2 高性能模型",
                "context_length": "128k",
                "max_output_length": "8k",
                "input_types": ["Text"],
                "output_types": ["Text"],
                "coding_score": 1377
            }
        }
    },
    APIKeyProvider.MOONSHOT: {
        "name": "月之暗面 Coding Plan",
        "website": "https://kimi.com",
        "supported_models": ["kimi-k2.5"],
        "logo_path": "/providers/moonshot-logo.png",
        "models": {
            "kimi-k2.5": {
                "display_name": "Kimi K2.5",
                "description": "Kimi K2.5 高性能模型",
                "context_length": "128k",
                "max_output_length": "128k",
                "input_types": ["Text", "Image", "Video"],
                "output_types": ["Text"],
                "coding_score": 1447
            }
        }
    },
    APIKeyProvider.MINIMAX: {
        "name": "MiniMax Coding Plan",
        "website": "https://www.minimaxi.com",
        "supported_models": ["minimax-m2.1"],
        "logo_path": "/providers/minimax-logo.png",
        "models": {
            "minimax-m2.1": {
                "display_name": "MiniMax M2.1",
                "description": "MiniMax M2.1 高性能代码模型，230B 总参数，10B 激活参数",
                "context_length": "196k",
                "max_output_length": "65k",
                "input_types": ["Text"],
                "output_types": ["Text"],
                "coding_score": 1409
            }
        }
    },
}

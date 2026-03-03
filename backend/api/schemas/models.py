from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional


class SharedBy(BaseModel):
    """共享者信息"""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "user_id": 1,
                "name": "user@example.com",
                "avatar_url": "https://example.com/avatar.jpg"
            }
        }
    )
    user_id: int = Field(description="共享者用户 ID")
    name: Optional[str] = Field(default=None, description="共享者名称")
    avatar_url: Optional[str] = Field(default=None, description="共享者头像 URL")


class ProviderInfo(BaseModel):
    """提供商信息"""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "code": "bigmodel",
                "name": "智谱 AI",
                "logo_path": "/providers/bigmodel-logo.png"
            }
        }
    )
    code: str = Field(description="提供商代码，如 'bigmodel'")
    name: str = Field(default="", description="提供商显示名称")
    logo_path: str = Field(description="提供商 Logo 路径")


class ModelInfo(BaseModel):
    """模型元数据"""
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "display_name": "BigModel: GLM-4.7",
                "model_name": "glm-4.7",
                "provider": "bigmodel",
                "description": "智谱 AI 最新一代旗舰模型，具备强大的理解和生成能力",
                "input_types": ["Text"],
                "output_types": ["Text"],
                "context_length": "128k",
                "max_output_length": "4k",
                "available_subscriptions": 3,
                "shared_by": [
                    {
                        "user_id": 1,
                        "name": "user@example.com",
                        "avatar_url": "https://example.com/avatar.jpg"
                    }
                ],
                "used_tokens": 1234567,
                "coding_score": 1441,
                "providers": [
                    {
                        "code": "bigmodel",
                        "logo_path": "/providers/bigmodel-logo.png"
                    },
                    {
                        "code": "zai",
                        "logo_path": "/providers/zai-logo.png"
                    }
                ],
                "subscription_platform_count": 2
            }
        }
    )
    display_name: str = Field(description="显示名称，如 'GLM-4.7'")
    model_name: str = Field(description="原始模型名称（模型 ID），如 'glm-4.7'")
    provider: str = Field(description="API 提供商标识，如 'bigmodel'")
    description: str = Field(description="模型描述")
    input_types: List[str] = Field(default_factory=lambda: ["Text"], description="输入类型列表")
    output_types: List[str] = Field(default_factory=lambda: ["Text"], description="输出类型列表")
    context_length: str = Field(description="上下文长度，如 '128k'")
    max_output_length: str = Field(description="最大输出长度，如 '4k'")
    available_subscriptions: int = Field(description="可用订阅数量")
    shared_by: List[SharedBy] = Field(description="共享者列表")
    used_tokens: Optional[int] = Field(default=None, description="已使用 Token 总量")
    coding_score: Optional[int] = Field(default=None, description="Coding 评分")
    providers: List[ProviderInfo] = Field(default_factory=list, description="可用提供商列表（code 和 logo_path）")
    subscription_platform_count: int = Field(default=0, description="订阅平台数量")
    model_logo_url: Optional[str] = Field(default=None, description="模型 Logo URL（来自全局模型配置）")


class ModelDiscoveryList(BaseModel):
    """模型发现列表响应"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "page": 1,
                "page_size": 10,
                "total": 3,
                "items": [
                    {
                        "display_name": "BigModel: GLM-4.7",
                        "model_name": "glm-4.7",
                        "provider": "bigmodel",
                        "description": "智谱 AI 最新一代旗舰模型，具备强大的理解和生成能力",
                        "input_type": "Text",
                        "output_type": "Text",
                        "context_length": "128k",
                        "max_output_length": "4k",
                        "available_subscriptions": 3,
                        "shared_by": [
                            {
                                "user_id": 1,
                                "name": "user@example.com",
                                "avatar_url": "https://example.com/avatar.jpg"
                            }
                        ]
                    }
                ]
            }
        }
    )
    page: int = Field(ge=1, description="当前页码")
    page_size: int = Field(ge=1, le=100, description="每页数量")
    total: int = Field(ge=0, description="模型总数")
    items: List[ModelInfo] = Field(description="模型列表")

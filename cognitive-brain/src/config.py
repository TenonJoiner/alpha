"""
配置管理模块

负责加载和管理 brain.yaml 配置
"""

from pathlib import Path
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DomainConfig(BaseModel):
    """领域配置"""
    
    name: str = Field(..., description="领域名称")
    description: str = Field(default="", description="领域描述")
    data_path: str = Field(..., description="数据目录路径")
    enabled: bool = Field(default=True, description="是否启用")
    
    class Config:
        frozen = False


class LLMConfig(BaseModel):
    """LLM 配置 (预留)"""
    
    provider: str = Field(default="claude", description="提供商")
    model: str = Field(default="claude-3-sonnet-20240229", description="模型")
    api_key: Optional[str] = Field(default=None, description="API Key")
    base_url: Optional[str] = Field(default=None, description="自定义 Base URL")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1)


class ServerConfig(BaseModel):
    """服务器配置"""
    
    name: str = Field(default="cognitive-brain")
    version: str = Field(default="0.1.0")
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1, le=65535)
    log_level: str = Field(default="info")
    workers: int = Field(default=1, ge=1)


class BrainConfig(BaseSettings):
    """
    Cognitive Brain 主配置类
    
    支持从 YAML 文件加载和从环境变量覆盖
    """
    
    model_config = SettingsConfigDict(
        env_prefix="BRAIN_",
        env_nested_delimiter="__",
        extra="ignore"
    )
    
    # 服务器配置
    server: ServerConfig = Field(default_factory=ServerConfig)
    
    # 路径配置
    data_root: Path = Field(default=Path("/data/knowledge-brains"))
    config_path: Path = Field(default=Path("brain.yaml"))
    
    # 领域配置
    domains: Dict[str, DomainConfig] = Field(default_factory=dict)
    
    # LLM 配置
    llm: LLMConfig = Field(default_factory=LLMConfig)
    
    # 功能开关
    enable_learning: bool = Field(default=True)
    enable_auto_index: bool = Field(default=True)
    max_concurrent_learning: int = Field(default=3, ge=1)
    
    @classmethod
    def from_yaml(cls, path: str | Path = "brain.yaml") -> "BrainConfig":
        """
        从 YAML 文件加载配置
        
        Args:
            path: 配置文件路径
            
        Returns:
            BrainConfig 实例
        """
        path = Path(path)
        
        if not path.exists():
            # 返回默认配置
            return cls()
        
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
        
        return cls.model_validate(data)
    
    def to_yaml(self, path: str | Path = None) -> None:
        """
        保存配置到 YAML 文件
        
        Args:
            path: 目标路径，默认为 self.config_path
        """
        path = Path(path) if path else self.config_path
        
        # 确保目录存在
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # 转换为字典并处理 Path 类型
        data = self.model_dump()
        
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(
                data, 
                f, 
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False
            )
    
    def get_domain_config(self, domain: str) -> Optional[DomainConfig]:
        """
        获取领域配置
        
        Args:
            domain: 领域标识
            
        Returns:
            DomainConfig 或 None
        """
        return self.domains.get(domain)
    
    def get_domain_data_path(self, domain: str) -> Optional[Path]:
        """
        获取领域数据路径
        
        Args:
            domain: 领域标识
            
        Returns:
            数据路径或 None
        """
        domain_config = self.domains.get(domain)
        if not domain_config:
            return None
        
        return self.data_root / domain_config.data_path
    
    def list_enabled_domains(self) -> List[str]:
        """
        获取启用的领域列表
        
        Returns:
            领域标识列表
        """
        return [
            key for key, config in self.domains.items()
            if config.enabled
        ]
    
    def add_domain(self, domain_id: str, config: DomainConfig) -> None:
        """
        添加领域配置
        
        Args:
            domain_id: 领域标识
            config: 领域配置
        """
        self.domains[domain_id] = config
    
    def remove_domain(self, domain_id: str) -> bool:
        """
        移除领域配置
        
        Args:
            domain_id: 领域标识
            
        Returns:
            是否成功移除
        """
        if domain_id in self.domains:
            del self.domains[domain_id]
            return True
        return False


# 全局配置实例
_config: Optional[BrainConfig] = None


def get_config() -> BrainConfig:
    """
    获取全局配置实例
    
    Returns:
        BrainConfig 实例
    """
    global _config
    if _config is None:
        _config = BrainConfig.from_yaml()
    return _config


def set_config(config: BrainConfig) -> None:
    """
    设置全局配置实例
    
    Args:
        config: 配置实例
    """
    global _config
    _config = config


def reload_config(path: str | Path = "brain.yaml") -> BrainConfig:
    """
    重新加载配置
    
    Args:
        path: 配置文件路径
        
    Returns:
        新的配置实例
    """
    global _config
    _config = BrainConfig.from_yaml(path)
    return _config


def create_default_config(path: str = "brain.yaml") -> BrainConfig:
    """
    创建默认配置文件
    
    Args:
        path: 配置文件路径
        
    Returns:
        默认配置实例
    """
    config = BrainConfig(
        server=ServerConfig(
            name="cognitive-brain",
            version="0.1.0",
            host="0.0.0.0",
            port=8000
        ),
        data_root=Path("/data/knowledge-brains"),
        domains={
            "storage-architect": DomainConfig(
                name="存储架构师",
                description="企业存储架构设计知识",
                data_path="storage-architect",
                enabled=True
            )
        }
    )
    config.to_yaml(path)
    return config

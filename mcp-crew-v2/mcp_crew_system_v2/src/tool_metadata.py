"""
Definição da classe ToolMetadata para uso em todo o sistema MCP-Crew
"""

from typing import Dict, Any
from dataclasses import dataclass, asdict

@dataclass
class ToolMetadata:
    """Metadados de uma ferramenta MCP"""
    name: str
    description: str
    parameters: Dict[str, Any]
    mcp_source: str
    last_updated: float
    cache_key: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolMetadata':
        return cls(**data)

"""
多模态智能体RAG系统

基于Qwen-Agent框架构建的多模态检索增强生成(RAG)系统，
支持PDF文档的文本、图片、表格等多模态内容解析、检索和问答。
"""

__version__ = "0.1.0"
__author__ = "Multimodal RAG Team"

from .agent import MultimodalRAGAgent

__all__ = [
    "MultimodalRAGAgent",
]

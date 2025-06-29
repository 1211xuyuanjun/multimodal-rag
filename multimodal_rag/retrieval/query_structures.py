"""
查询相关数据结构

定义查询分解和执行过程中使用的数据结构。
"""

from typing import List, Optional
from dataclasses import dataclass


@dataclass
class QueryIntent:
    """查询意图分析结果"""
    intent_type: str  # 'simple', 'complex', 'multi_aspect', 'comparative'
    complexity_score: float  # 0-10的复杂度评分
    key_concepts: List[str]  # 关键概念
    question_type: str  # 'factual', 'analytical', 'procedural', 'comparative'
    requires_decomposition: bool  # 是否需要分解
    reasoning: str  # 分析推理过程


@dataclass
class SubQuery:
    """子查询"""
    query: str  # 子查询文本
    intent: str  # 子查询意图
    priority: int  # 优先级 (1-5)
    depends_on: List[int] = None  # 依赖的子查询索引
    context_needed: bool = False  # 是否需要前面查询的上下文


@dataclass
class DecompositionResult:
    """查询分解结果"""
    original_query: str
    intent: QueryIntent
    sub_queries: List[SubQuery]
    execution_plan: List[int]  # 执行顺序

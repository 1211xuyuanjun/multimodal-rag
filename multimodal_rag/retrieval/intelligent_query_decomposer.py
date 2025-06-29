"""
智能查询分解器

实现复杂查询的理解和分解，提升RAG系统对复杂问题的处理能力。
"""

import re
import json
import sys
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

# 添加Qwen-Agent到路径
sys.path.append(str(Path(__file__).parent.parent.parent / "Qwen-Agent"))

from qwen_agent.llm.base import BaseChatModel
from qwen_agent.llm.schema import Message, USER, ASSISTANT

from .query_structures import QueryIntent, SubQuery, DecompositionResult

logger = logging.getLogger(__name__)

class IntelligentQueryDecomposer:
    """
    智能查询分解器
    
    功能：
    1. 查询意图理解 - 分析用户问题的真实意图和复杂度
    2. 智能分解 - 将复杂问题分解为多个子问题
    3. 执行规划 - 规划子查询的执行顺序和依赖关系
    4. 上下文管理 - 管理子查询间的上下文传递
    """
    
    def __init__(
        self,
        llm: Optional[BaseChatModel] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化智能查询分解器
        
        Args:
            llm: 语言模型
            config: 配置参数
        """
        self.llm = llm
        self.config = config or {
            'decomposition_threshold': 6.0,  # 触发分解的复杂度阈值
            'max_sub_queries': 5,  # 最大子查询数量
            'enable_context_passing': True,  # 启用上下文传递
            'min_query_length': 10,  # 最小查询长度
        }
    
    def analyze_and_decompose(self, query: str) -> DecompositionResult:
        """
        分析查询并进行分解
        
        Args:
            query: 原始查询
            
        Returns:
            分解结果
        """
        logger.info(f"开始分析查询: {query[:50]}...")
        
        # 1. 查询意图理解
        intent = self._analyze_query_intent(query)
        
        # 2. 判断是否需要分解
        if not intent.requires_decomposition:
            logger.info("查询无需分解，返回原始查询")
            return DecompositionResult(
                original_query=query,
                intent=intent,
                sub_queries=[SubQuery(query=query, intent="simple", priority=1)],
                execution_plan=[0]
            )
        
        # 3. 执行查询分解
        sub_queries = self._decompose_query(query, intent)
        
        # 4. 生成执行计划
        execution_plan = self._generate_execution_plan(sub_queries)
        
        result = DecompositionResult(
            original_query=query,
            intent=intent,
            sub_queries=sub_queries,
            execution_plan=execution_plan
        )
        
        logger.info(f"查询分解完成: 生成{len(sub_queries)}个子查询")
        return result
    
    def _analyze_query_intent(self, query: str) -> QueryIntent:
        """
        分析查询意图
        
        Args:
            query: 查询文本
            
        Returns:
            查询意图分析结果
        """
        if not self.llm:
            # 简单的规则基础分析
            return self._rule_based_intent_analysis(query)
        
        try:
            prompt = f"""请分析以下查询的意图和复杂度，并以JSON格式返回分析结果：

查询：{query}

请分析以下方面：
1. 意图类型：simple(简单查询), complex(复杂查询), multi_aspect(多方面查询), comparative(比较查询)
2. 复杂度评分：0-10分，考虑查询的复杂程度、涉及概念数量、逻辑关系等
3. 关键概念：提取查询中的主要概念和实体
4. 问题类型：factual(事实性), analytical(分析性), procedural(程序性), comparative(比较性)
5. 是否需要分解：复杂度>6分或涉及多个独立概念时需要分解
6. 分析推理：简要说明分析过程

返回JSON格式：
{{
    "intent_type": "类型",
    "complexity_score": 分数,
    "key_concepts": ["概念1", "概念2"],
    "question_type": "类型",
    "requires_decomposition": true/false,
    "reasoning": "分析推理过程"
}}"""

            messages = [Message(USER, prompt)]
            
            response = None
            for response in self.llm.chat(messages):
                continue
            
            if response and response[-1].role == ASSISTANT:
                content = response[-1].content.strip()
                
                # 提取JSON内容
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    intent_data = json.loads(json_str)
                    
                    return QueryIntent(
                        intent_type=intent_data.get('intent_type', 'simple'),
                        complexity_score=float(intent_data.get('complexity_score', 3.0)),
                        key_concepts=intent_data.get('key_concepts', []),
                        question_type=intent_data.get('question_type', 'factual'),
                        requires_decomposition=intent_data.get('requires_decomposition', False),
                        reasoning=intent_data.get('reasoning', '')
                    )
        
        except Exception as e:
            logger.error(f"LLM意图分析失败: {str(e)}")
        
        # 回退到规则分析
        return self._rule_based_intent_analysis(query)
    
    def _rule_based_intent_analysis(self, query: str) -> QueryIntent:
        """
        基于规则的意图分析
        
        Args:
            query: 查询文本
            
        Returns:
            查询意图
        """
        # 计算复杂度
        complexity_score = 0.0
        
        # 长度因子
        complexity_score += min(len(query) / 50, 3.0)
        
        # 关键词因子
        complex_keywords = ['比较', '对比', '分析', '评估', '总结', '归纳', '如何', '为什么', '原因', '影响', '关系']
        for keyword in complex_keywords:
            if keyword in query:
                complexity_score += 1.5
        
        # 连接词因子
        connectors = ['和', '与', '以及', '同时', '另外', '此外', '而且', '并且']
        for connector in connectors:
            if connector in query:
                complexity_score += 1.0
        
        # 问号数量
        complexity_score += query.count('?') * 0.5 + query.count('？') * 0.5
        
        # 确定意图类型
        if any(word in query for word in ['比较', '对比', '区别']):
            intent_type = 'comparative'
        elif any(word in query for word in ['和', '与', '以及']) and complexity_score > 5:
            intent_type = 'multi_aspect'
        elif complexity_score > 6:
            intent_type = 'complex'
        else:
            intent_type = 'simple'
        
        # 确定问题类型
        if any(word in query for word in ['如何', '怎么', '步骤', '方法']):
            question_type = 'procedural'
        elif any(word in query for word in ['为什么', '原因', '分析', '评估']):
            question_type = 'analytical'
        elif any(word in query for word in ['比较', '对比', '区别']):
            question_type = 'comparative'
        else:
            question_type = 'factual'
        
        # 提取关键概念（简单实现）
        key_concepts = []
        # 这里可以添加更复杂的NER逻辑
        words = query.split()
        for word in words:
            if len(word) > 2 and word not in ['如何', '为什么', '什么', '哪些', '怎么']:
                key_concepts.append(word)
        
        return QueryIntent(
            intent_type=intent_type,
            complexity_score=min(complexity_score, 10.0),
            key_concepts=key_concepts[:5],  # 最多5个关键概念
            question_type=question_type,
            requires_decomposition=complexity_score >= self.config['decomposition_threshold'],
            reasoning=f"基于规则分析，复杂度评分: {complexity_score:.1f}"
        )

    def _decompose_query(self, query: str, intent: QueryIntent) -> List[SubQuery]:
        """
        分解查询为子查询

        Args:
            query: 原始查询
            intent: 查询意图

        Returns:
            子查询列表
        """
        if not self.llm:
            return self._rule_based_decomposition(query, intent)

        try:
            prompt = f"""请将以下复杂查询分解为多个具体的子查询，每个子查询应该专注于一个特定的方面：

原始查询：{query}
查询类型：{intent.intent_type}
关键概念：{', '.join(intent.key_concepts)}

分解要求：
1. 每个子查询应该是独立的、具体的问题
2. 子查询之间应该有逻辑关系，能够组合回答原始问题
3. 按照逻辑顺序排列子查询
4. 最多生成{self.config['max_sub_queries']}个子查询
5. 每个子查询应该足够具体，能够通过文档检索找到答案

请以JSON格式返回分解结果：
{{
    "sub_queries": [
        {{
            "query": "具体的子查询文本",
            "intent": "子查询的目的说明",
            "priority": 1-5的优先级,
            "depends_on": [依赖的子查询索引列表，如果没有依赖则为空],
            "context_needed": true/false是否需要前面查询的上下文
        }}
    ]
}}

示例：
如果原始查询是"比较Python和Java的性能差异，并分析各自的优缺点"
可能的分解：
1. "Python编程语言的性能特点和执行速度"
2. "Java编程语言的性能特点和执行速度"
3. "Python编程语言的优点和缺点"
4. "Java编程语言的优点和缺点"
5. "Python和Java性能对比分析"（依赖前面的查询结果）"""

            messages = [Message(USER, prompt)]

            response = None
            for response in self.llm.chat(messages):
                continue

            if response and response[-1].role == ASSISTANT:
                content = response[-1].content.strip()

                # 提取JSON内容
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    decomp_data = json.loads(json_str)

                    sub_queries = []
                    for i, sq_data in enumerate(decomp_data.get('sub_queries', [])):
                        sub_query = SubQuery(
                            query=sq_data.get('query', ''),
                            intent=sq_data.get('intent', ''),
                            priority=sq_data.get('priority', 3),
                            depends_on=sq_data.get('depends_on', []),
                            context_needed=sq_data.get('context_needed', False)
                        )
                        sub_queries.append(sub_query)

                    return sub_queries[:self.config['max_sub_queries']]

        except Exception as e:
            logger.error(f"LLM查询分解失败: {str(e)}")

        # 回退到规则分解
        return self._rule_based_decomposition(query, intent)

    def _rule_based_decomposition(self, query: str, intent: QueryIntent) -> List[SubQuery]:
        """
        基于规则的查询分解

        Args:
            query: 原始查询
            intent: 查询意图

        Returns:
            子查询列表
        """
        sub_queries = []

        if intent.intent_type == 'comparative':
            # 比较类查询分解
            sub_queries = self._decompose_comparative_query(query, intent)
        elif intent.intent_type == 'multi_aspect':
            # 多方面查询分解
            sub_queries = self._decompose_multi_aspect_query(query, intent)
        elif intent.intent_type == 'complex':
            # 复杂查询分解
            sub_queries = self._decompose_complex_query(query, intent)
        else:
            # 简单查询，不分解
            sub_queries = [SubQuery(query=query, intent="simple", priority=1)]

        return sub_queries

    def _decompose_comparative_query(self, query: str, intent: QueryIntent) -> List[SubQuery]:
        """分解比较类查询"""
        sub_queries = []

        # 提取比较对象
        concepts = intent.key_concepts
        if len(concepts) >= 2:
            # 为每个概念创建单独的查询
            for i, concept in enumerate(concepts[:2]):  # 最多比较两个对象
                sub_queries.append(SubQuery(
                    query=f"{concept}的特点和属性",
                    intent=f"了解{concept}的基本信息",
                    priority=1
                ))

            # 添加比较查询
            if len(concepts) >= 2:
                sub_queries.append(SubQuery(
                    query=f"{concepts[0]}和{concepts[1]}的比较分析",
                    intent="比较分析两者的差异",
                    priority=2,
                    depends_on=[0, 1],
                    context_needed=True
                ))

        return sub_queries

    def _decompose_multi_aspect_query(self, query: str, intent: QueryIntent) -> List[SubQuery]:
        """分解多方面查询"""
        sub_queries = []

        # 为每个关键概念创建查询
        for i, concept in enumerate(intent.key_concepts[:3]):  # 最多3个方面
            sub_queries.append(SubQuery(
                query=f"{concept}的详细信息和相关内容",
                intent=f"了解{concept}的具体情况",
                priority=1
            ))

        # 如果有多个概念，添加综合查询
        if len(intent.key_concepts) > 1:
            concepts_str = "、".join(intent.key_concepts[:3])
            sub_queries.append(SubQuery(
                query=f"{concepts_str}之间的关系和综合分析",
                intent="综合分析各方面的关系",
                priority=2,
                depends_on=list(range(len(sub_queries))),
                context_needed=True
            ))

        return sub_queries

    def _decompose_complex_query(self, query: str, intent: QueryIntent) -> List[SubQuery]:
        """分解复杂查询"""
        sub_queries = []

        # 基于问题类型分解
        if intent.question_type == 'procedural':
            # 程序性问题：分解为步骤
            sub_queries.append(SubQuery(
                query=f"{intent.key_concepts[0] if intent.key_concepts else ''}的基本概念和定义",
                intent="了解基本概念",
                priority=1
            ))
            sub_queries.append(SubQuery(
                query=f"{query}的具体步骤和方法",
                intent="获取具体操作步骤",
                priority=2,
                depends_on=[0],
                context_needed=True
            ))
        elif intent.question_type == 'analytical':
            # 分析性问题：分解为因果关系
            if intent.key_concepts:
                main_concept = intent.key_concepts[0]
                sub_queries.append(SubQuery(
                    query=f"{main_concept}的基本情况和背景",
                    intent="了解背景信息",
                    priority=1
                ))
                sub_queries.append(SubQuery(
                    query=f"{main_concept}的影响因素和原因分析",
                    intent="分析影响因素",
                    priority=2,
                    depends_on=[0],
                    context_needed=True
                ))
        else:
            # 其他复杂查询：按关键概念分解
            for concept in intent.key_concepts[:2]:
                sub_queries.append(SubQuery(
                    query=f"{concept}的详细信息",
                    intent=f"了解{concept}",
                    priority=1
                ))

        return sub_queries

    def _generate_execution_plan(self, sub_queries: List[SubQuery]) -> List[int]:
        """
        生成子查询执行计划

        Args:
            sub_queries: 子查询列表

        Returns:
            执行顺序索引列表
        """
        if not sub_queries:
            return []

        # 构建依赖图
        dependency_graph = {}
        for i, sq in enumerate(sub_queries):
            dependency_graph[i] = sq.depends_on or []

        # 拓扑排序
        execution_plan = []
        visited = set()
        temp_visited = set()

        def dfs(node):
            if node in temp_visited:
                # 检测到循环依赖，按优先级排序
                logger.warning(f"检测到循环依赖，节点 {node}")
                return
            if node in visited:
                return

            temp_visited.add(node)

            # 先访问依赖的节点
            for dep in dependency_graph.get(node, []):
                if dep < len(sub_queries):  # 确保依赖索引有效
                    dfs(dep)

            temp_visited.remove(node)
            visited.add(node)
            execution_plan.append(node)

        # 按优先级排序节点
        nodes_by_priority = sorted(range(len(sub_queries)),
                                 key=lambda x: sub_queries[x].priority)

        for node in nodes_by_priority:
            if node not in visited:
                dfs(node)

        return execution_plan

"""
查询优化器

实现查询扩展、重写和自我批判机制，提升检索准确性。
"""

import re
import sys
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import logging

# 添加Qwen-Agent到路径
sys.path.append(str(Path(__file__).parent.parent.parent / "Qwen-Agent"))

from qwen_agent.llm.base import BaseChatModel
from qwen_agent.llm.schema import Message, USER, ASSISTANT

from ..config import QUERY_OPTIMIZATION_CONFIG

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """
    查询优化器
    
    功能：
    1. 查询扩展 - 添加同义词和相关词
    2. 查询重写 - 改写查询以提高检索效果
    3. 自我批判 - 评估和改进查询质量
    4. 多查询生成 - 生成多个候选查询
    """
    
    def __init__(
        self,
        llm: Optional[BaseChatModel] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化查询优化器
        
        Args:
            llm: 语言模型
            config: 配置参数
        """
        self.llm = llm
        self.config = config or QUERY_OPTIMIZATION_CONFIG
        
        # 同义词词典（简单示例）
        self.synonyms = {
            '图片': ['图像', '照片', '图表', '插图'],
            '表格': ['表单', '数据表', '统计表'],
            '文档': ['文件', '资料', '材料'],
            '内容': ['信息', '数据', '资料'],
            '总结': ['概括', '摘要', '归纳'],
            '分析': ['解析', '研究', '评估'],
        }
    
    def optimize_query(self, query: str) -> List[str]:
        """
        优化查询

        Args:
            query: 原始查询

        Returns:
            优化后的查询列表
        """
        logger.info(f"开始优化查询: {query}")

        optimized_queries = [query]  # 包含原始查询

        # 使用LLM生成多样化查询（优先）
        if self.llm and self.config.get('enable_llm_diversification', True):
            diverse_queries = self._generate_diverse_queries(query)
            optimized_queries.extend(diverse_queries)
        else:
            # 回退到传统方法
            # 查询扩展
            if self.config.get('enable_query_expansion', True):
                expanded_queries = self._expand_query(query)
                optimized_queries.extend(expanded_queries)

            # 查询重写
            if self.config.get('enable_query_rewrite', True):
                rewritten_queries = self._rewrite_query(query)
                optimized_queries.extend(rewritten_queries)

        # 智能去重并限制数量
        unique_queries = self._intelligent_deduplication(optimized_queries)
        max_queries = self.config.get('max_expansions', 3)

        final_queries = unique_queries[:max_queries + 1]  # +1 for original query

        logger.info(f"查询优化完成: 生成{len(final_queries)}个查询")
        return final_queries
    
    def _expand_query(self, query: str) -> List[str]:
        """
        查询扩展
        
        Args:
            query: 原始查询
            
        Returns:
            扩展后的查询列表
        """
        expanded_queries = []
        
        # 同义词扩展
        synonym_query = self._expand_with_synonyms(query)
        if synonym_query != query:
            expanded_queries.append(synonym_query)
        
        # 相关词扩展
        related_query = self._expand_with_related_terms(query)
        if related_query != query:
            expanded_queries.append(related_query)
        
        # 上下文扩展
        context_query = self._expand_with_context(query)
        if context_query != query:
            expanded_queries.append(context_query)
        
        return expanded_queries
    
    def _expand_with_synonyms(self, query: str) -> str:
        """使用同义词扩展查询"""
        words = query.split()
        expanded_words = []
        
        for word in words:
            expanded_words.append(word)
            
            # 查找同义词
            for key, synonyms in self.synonyms.items():
                if key in word or word in key:
                    # 添加一个同义词
                    if synonyms:
                        expanded_words.append(synonyms[0])
                    break
        
        return ' '.join(expanded_words)
    
    def _expand_with_related_terms(self, query: str) -> str:
        """使用相关词扩展查询"""
        # 基于查询内容添加相关词
        related_terms = []
        
        if any(word in query for word in ['图片', '图像', '照片']):
            related_terms.extend(['视觉', '图表', '插图'])
        
        if any(word in query for word in ['表格', '数据']):
            related_terms.extend(['统计', '数值', '表单'])
        
        if any(word in query for word in ['总结', '概括']):
            related_terms.extend(['摘要', '要点', '核心'])
        
        if related_terms:
            return query + ' ' + ' '.join(related_terms[:2])  # 最多添加2个相关词
        
        return query
    
    def _expand_with_context(self, query: str) -> str:
        """使用上下文扩展查询"""
        # 添加上下文信息
        context_additions = []
        
        # 如果查询很短，添加更多描述性词汇
        if len(query.split()) <= 2:
            context_additions.append('详细信息')
        
        # 如果是问句，添加相关的陈述性词汇
        if '?' in query or '？' in query:
            context_additions.append('解释说明')
        
        if context_additions:
            return query + ' ' + ' '.join(context_additions)
        
        return query
    
    def _rewrite_query(self, query: str) -> List[str]:
        """
        查询重写
        
        Args:
            query: 原始查询
            
        Returns:
            重写后的查询列表
        """
        rewritten_queries = []
        
        # 转换为不同的表达方式
        if self.llm:
            llm_rewritten = self._llm_rewrite_query(query)
            rewritten_queries.extend(llm_rewritten)
        else:
            # 使用规则重写
            rule_rewritten = self._rule_based_rewrite(query)
            rewritten_queries.extend(rule_rewritten)
        
        return rewritten_queries
    
    def _rule_based_rewrite(self, query: str) -> List[str]:
        """基于规则的查询重写"""
        rewritten = []
        
        # 问句转陈述句
        if '?' in query or '？' in query:
            statement = query.replace('?', '').replace('？', '').strip()
            if statement:
                rewritten.append(statement)
        
        # 添加动作词
        action_words = ['显示', '说明', '描述', '解释']
        for action in action_words:
            if action not in query:
                rewritten.append(f"{action}{query}")
                break
        
        return rewritten
    
    def _llm_rewrite_query(self, query: str) -> List[str]:
        """使用LLM重写查询"""
        if not self.llm:
            return []
        
        try:
            prompt = f"""请将以下查询重写为2-3个不同的表达方式，保持原意不变但使用不同的词汇和句式：

原查询：{query}

要求：
1. 保持查询的核心意图
2. 使用不同的词汇和表达方式
3. 每行一个重写结果
4. 不要添加额外的解释

重写结果："""

            messages = [Message(USER, prompt)]
            
            response = None
            for response in self.llm.chat(messages):
                continue
            
            if response and response[-1].role == ASSISTANT:
                content = response[-1].content.strip()
                
                # 解析重写结果
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                
                # 过滤掉包含"重写结果"等标题的行
                rewritten_queries = []
                for line in lines:
                    if not any(keyword in line for keyword in ['重写结果', '原查询', '要求']):
                        # 移除序号
                        line = re.sub(r'^\d+[.、]\s*', '', line)
                        if line and line != query:
                            rewritten_queries.append(line)
                
                return rewritten_queries[:2]  # 最多返回2个重写结果
        
        except Exception as e:
            logger.error(f"LLM查询重写失败: {str(e)}")
        
        return []
    
    def _self_critique_query(self, query: str) -> List[str]:
        """
        自我批判查询
        
        Args:
            query: 原始查询
            
        Returns:
            改进后的查询列表
        """
        if not self.llm:
            return []
        
        try:
            prompt = f"""请分析以下查询的质量，并提供改进建议：

查询：{query}

请从以下角度分析：
1. 查询是否清晰明确？
2. 是否包含足够的关键信息？
3. 是否可能存在歧义？
4. 如何改进以获得更好的检索结果？

基于分析结果，请提供1-2个改进后的查询版本："""

            messages = [Message(USER, prompt)]
            
            response = None
            for response in self.llm.chat(messages):
                continue
            
            if response and response[-1].role == ASSISTANT:
                content = response[-1].content.strip()
                
                # 提取改进后的查询
                improved_queries = self._extract_improved_queries(content)
                return improved_queries
        
        except Exception as e:
            logger.error(f"自我批判查询失败: {str(e)}")
        
        return []
    
    def _extract_improved_queries(self, content: str) -> List[str]:
        """从LLM响应中提取改进后的查询"""
        lines = content.split('\n')
        improved_queries = []
        
        # 查找包含改进查询的行
        for line in lines:
            line = line.strip()
            
            # 跳过分析性文本
            if any(keyword in line for keyword in ['分析', '建议', '角度', '结果', '版本']):
                continue
            
            # 移除序号和标点
            line = re.sub(r'^\d+[.、]\s*', '', line)
            line = re.sub(r'^[改进后的查询|改进版本|建议查询][:：]\s*', '', line)
            
            # 如果是有效的查询（不是分析文本）
            if line and len(line) > 3 and not line.endswith('？') and not line.endswith('?'):
                if not any(keyword in line for keyword in ['分析', '建议', '可以', '应该', '需要']):
                    improved_queries.append(line)
        
        return improved_queries[:2]  # 最多返回2个改进查询

    def _generate_diverse_queries(self, query: str) -> List[str]:
        """
        生成多样化查询

        Args:
            query: 原始查询

        Returns:
            多样化查询列表
        """
        if not self.llm:
            return []

        try:
            prompt = f"""请基于以下查询生成3个不同角度和表达方式的查询变体，确保每个查询都有明显的差异性：

原查询：{query}

要求：
1. 每个查询变体应该从不同角度或层面来表达相同的信息需求
2. 使用不同的关键词、句式结构和表达方式
3. 保持查询的核心意图不变
4. 确保查询之间有明显差异，避免重复相似的表达
5. 每行一个查询，不要添加序号或解释

生成策略：
- 第一个：改变问题的焦点或范围
- 第二个：使用不同的词汇和句式结构
- 第三个：从更具体或更抽象的角度表达

查询变体："""

            messages = [Message(USER, prompt)]

            response = None
            for response in self.llm.chat(messages):
                continue

            if response and response[-1].role == ASSISTANT:
                content = response[-1].content.strip()

                # 解析查询变体
                lines = [line.strip() for line in content.split('\n') if line.strip()]

                diverse_queries = []
                for line in lines:
                    # 清理格式
                    line = re.sub(r'^\d+[.、]\s*', '', line)  # 移除序号
                    line = re.sub(r'^[查询变体|变体][:：]\s*', '', line)  # 移除标题
                    line = line.strip('- ')  # 移除破折号

                    if line and line != query and len(line) > 5:
                        # 检查是否与原查询和已有查询足够不同
                        if self._is_sufficiently_different(line, [query] + diverse_queries):
                            diverse_queries.append(line)

                return diverse_queries[:3]  # 最多返回3个多样化查询

        except Exception as e:
            logger.error(f"生成多样化查询失败: {str(e)}")

        return []

    def _is_sufficiently_different(self, new_query: str, existing_queries: List[str]) -> bool:
        """
        检查新查询是否与现有查询足够不同

        Args:
            new_query: 新查询
            existing_queries: 现有查询列表

        Returns:
            是否足够不同
        """
        new_words = set(new_query.lower().split())

        for existing_query in existing_queries:
            existing_words = set(existing_query.lower().split())

            # 计算词汇重叠率
            intersection = new_words.intersection(existing_words)
            union = new_words.union(existing_words)

            if len(union) == 0:
                continue

            overlap_ratio = len(intersection) / len(union)

            # 如果重叠率超过70%，认为过于相似
            if overlap_ratio > 0.7:
                return False

        return True

    def _intelligent_deduplication(self, queries: List[str]) -> List[str]:
        """
        智能去重

        Args:
            queries: 查询列表

        Returns:
            去重后的查询列表
        """
        if not queries:
            return []

        unique_queries = [queries[0]]  # 保留第一个（原始查询）

        for query in queries[1:]:
            if self._is_sufficiently_different(query, unique_queries):
                unique_queries.append(query)

        return unique_queries

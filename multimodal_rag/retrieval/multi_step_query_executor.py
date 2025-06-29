"""
多步查询执行器

负责按照执行计划逐步执行子查询，管理上下文传递和结果累积。
"""

from typing import List, Dict, Any, Optional
import logging

from .query_structures import DecompositionResult, SubQuery

logger = logging.getLogger(__name__)


class MultiStepQueryExecutor:
    """
    多步查询执行器

    负责按照执行计划逐步执行子查询，管理上下文传递和结果累积。
    """

    def __init__(self, retriever, config: Optional[Dict[str, Any]] = None):
        """
        初始化多步查询执行器

        Args:
            retriever: 检索器实例
            config: 配置参数
        """
        self.retriever = retriever
        self.config = config or {
            'max_context_length': 1000,  # 最大上下文长度
            'context_overlap': 0.2,  # 上下文重叠比例
            'enable_result_fusion': True,  # 启用结果融合
        }
        self.execution_context = {}  # 执行上下文
        self.accumulated_results = []  # 累积结果

    def execute_decomposed_query(self, decomposition: DecompositionResult, **kwargs) -> List[Dict[str, Any]]:
        """
        执行分解后的查询

        Args:
            decomposition: 查询分解结果
            **kwargs: 检索参数

        Returns:
            累积的检索结果
        """
        logger.info(f"开始执行多步查询，共{len(decomposition.sub_queries)}个子查询")

        self.execution_context = {}
        self.accumulated_results = []

        # 按执行计划顺序执行
        for step, query_idx in enumerate(decomposition.execution_plan):
            if query_idx >= len(decomposition.sub_queries):
                logger.warning(f"无效的查询索引: {query_idx}")
                continue

            sub_query = decomposition.sub_queries[query_idx]
            logger.info(f"执行第{step+1}步: {sub_query.query[:50]}...")

            # 构建查询上下文
            query_with_context = self._build_query_context(sub_query, query_idx)

            # 执行检索
            try:
                results = self.retriever.retrieve(query_with_context, **kwargs)

                # 存储结果和上下文
                self.execution_context[query_idx] = {
                    'query': sub_query.query,
                    'results': results,
                    'step': step
                }

                # 累积结果
                self.accumulated_results.extend(results)

                logger.info(f"第{step+1}步完成，获得{len(results)}个结果")

            except Exception as e:
                logger.error(f"执行子查询失败: {str(e)}")
                continue

        # 结果去重和融合
        final_results = self._fuse_results(self.accumulated_results)

        logger.info(f"多步查询执行完成，最终返回{len(final_results)}个结果")
        return final_results

    def _build_query_context(self, sub_query: SubQuery, query_idx: int) -> str:
        """
        构建带上下文的查询

        Args:
            sub_query: 子查询
            query_idx: 查询索引

        Returns:
            带上下文的查询文本
        """
        query = sub_query.query

        if not sub_query.context_needed or not sub_query.depends_on:
            return query

        # 收集依赖查询的上下文
        context_parts = []
        for dep_idx in sub_query.depends_on:
            if dep_idx in self.execution_context:
                dep_context = self.execution_context[dep_idx]
                # 提取关键信息作为上下文
                if dep_context['results']:
                    # 取前几个结果的摘要作为上下文
                    for result in dep_context['results'][:2]:
                        if 'content' in result:
                            content = result['content'][:200]  # 限制长度
                            context_parts.append(f"相关信息: {content}")

        if context_parts:
            context = " ".join(context_parts)
            # 限制上下文长度
            if len(context) > self.config['max_context_length']:
                context = context[:self.config['max_context_length']] + "..."

            query_with_context = f"{context}\n\n基于以上信息，{query}"
            return query_with_context

        return query

    def _fuse_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        融合多步查询结果

        Args:
            results: 原始结果列表

        Returns:
            融合后的结果列表
        """
        if not self.config.get('enable_result_fusion', True):
            return results

        # 简单去重：基于内容相似度
        unique_results = []
        seen_contents = set()

        for result in results:
            content = result.get('content', '')
            # 简单的内容指纹
            content_fingerprint = content[:100] if content else ''

            if content_fingerprint not in seen_contents:
                seen_contents.add(content_fingerprint)
                unique_results.append(result)

        # 按相关性分数排序
        unique_results.sort(key=lambda x: x.get('score', 0), reverse=True)

        return unique_results

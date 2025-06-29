"""
智能查询处理器

整合查询分解、多步执行和结果汇总的完整查询处理流程。
"""

import sys
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

# 添加Qwen-Agent到路径
sys.path.append(str(Path(__file__).parent.parent.parent / "Qwen-Agent"))

from qwen_agent.llm.base import BaseChatModel

from .intelligent_query_decomposer import IntelligentQueryDecomposer
from .multi_step_query_executor import MultiStepQueryExecutor
from .result_synthesizer import ResultSynthesizer

logger = logging.getLogger(__name__)

class IntelligentQueryProcessor:
    """
    智能查询处理器
    
    整合了查询理解、分解、执行和汇总的完整流程，
    能够处理复杂的多方面查询并生成连贯的答案。
    """
    
    def __init__(
        self,
        retriever,
        llm: Optional[BaseChatModel] = None,
        multimodal_llm: Optional[BaseChatModel] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化智能查询处理器

        Args:
            retriever: 检索器实例
            llm: 语言模型
            multimodal_llm: 多模态语言模型
            config: 配置参数
        """
        self.retriever = retriever
        self.llm = llm
        self.multimodal_llm = multimodal_llm
        self.config = config or {
            'enable_decomposition': True,  # 启用查询分解
            'decomposition_threshold': 6.0,  # 分解阈值
            'max_sub_queries': 5,  # 最大子查询数量
            'enable_synthesis': True,  # 启用结果汇总
            'fallback_to_simple': True,  # 失败时回退到简单查询
        }
        
        # 初始化组件
        self.decomposer = IntelligentQueryDecomposer(
            llm=llm,
            config={
                'decomposition_threshold': self.config.get('decomposition_threshold', 6.0),
                'max_sub_queries': self.config.get('max_sub_queries', 5),
                'enable_context_passing': True,
                'min_query_length': 10,
            }
        )
        
        self.executor = MultiStepQueryExecutor(
            retriever=retriever,
            config={
                'max_context_length': 1000,
                'context_overlap': 0.2,
                'enable_result_fusion': True,
            }
        )
        
        self.synthesizer = ResultSynthesizer(
            llm=llm,
            multimodal_llm=multimodal_llm,
            config={
                'max_synthesis_length': 2000,
                'enable_logical_flow': True,
                'include_source_references': True,
                'synthesis_style': 'comprehensive',
            }
        )
    
    def process_query(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        处理查询并返回结果
        
        Args:
            query: 用户查询
            **kwargs: 检索参数
            
        Returns:
            处理结果字典，包含答案、分解信息、检索结果等
        """
        logger.info(f"开始处理查询: {query[:50]}...")
        
        try:
            # 1. 查询分解
            if self.config.get('enable_decomposition', True):
                decomposition = self.decomposer.analyze_and_decompose(query)
                
                # 检查是否需要分解
                if decomposition.intent.requires_decomposition and len(decomposition.sub_queries) > 1:
                    return self._process_complex_query(query, decomposition, **kwargs)
                else:
                    return self._process_simple_query(query, **kwargs)
            else:
                return self._process_simple_query(query, **kwargs)
        
        except Exception as e:
            logger.error(f"查询处理失败: {str(e)}")
            
            # 回退到简单查询
            if self.config.get('fallback_to_simple', True):
                logger.info("回退到简单查询处理")
                return self._process_simple_query(query, **kwargs)
            else:
                return {
                    'answer': f"查询处理过程中出现错误: {str(e)}",
                    'query_type': 'error',
                    'sub_queries': [],
                    'retrieved_chunks': [],
                    'processing_info': {
                        'error': str(e),
                        'fallback_used': False
                    }
                }
    
    def _process_complex_query(
        self,
        query: str,
        decomposition,
        **kwargs
    ) -> Dict[str, Any]:
        """
        处理复杂查询
        
        Args:
            query: 原始查询
            decomposition: 查询分解结果
            **kwargs: 检索参数
            
        Returns:
            处理结果
        """
        logger.info(f"处理复杂查询，分解为{len(decomposition.sub_queries)}个子查询")
        
        # 2. 多步执行
        all_results = self.executor.execute_decomposed_query(decomposition, **kwargs)
        
        # 收集子查询结果
        sub_results = {}
        for query_idx, context in self.executor.execution_context.items():
            sub_results[query_idx] = context['results']
        
        # 3. 结果汇总
        if self.config.get('enable_synthesis', True) and len(sub_results) > 1:
            answer = self.synthesizer.synthesize_results(query, decomposition, sub_results)
        else:
            # 简单合并结果
            answer = self._simple_result_combination(all_results)
        
        return {
            'answer': answer,
            'query_type': 'complex',
            'original_query': query,
            'intent_analysis': {
                'intent_type': decomposition.intent.intent_type,
                'complexity_score': decomposition.intent.complexity_score,
                'key_concepts': decomposition.intent.key_concepts,
                'question_type': decomposition.intent.question_type,
                'reasoning': decomposition.intent.reasoning
            },
            'sub_queries': [
                {
                    'query': sq.query,
                    'intent': sq.intent,
                    'priority': sq.priority,
                    'results_count': len(sub_results.get(i, []))
                }
                for i, sq in enumerate(decomposition.sub_queries)
            ],
            'execution_plan': decomposition.execution_plan,
            'retrieved_chunks': all_results,
            'processing_info': {
                'decomposition_used': True,
                'synthesis_used': self.config.get('enable_synthesis', True),
                'total_sub_queries': len(decomposition.sub_queries),
                'total_results': len(all_results)
            }
        }
    
    def _process_simple_query(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        处理简单查询
        
        Args:
            query: 查询文本
            **kwargs: 检索参数
            
        Returns:
            处理结果
        """
        logger.info("处理简单查询")
        
        # 直接检索
        results = self.retriever.retrieve(query, **kwargs)
        
        # 生成简单答案
        answer = self.synthesizer._generate_simple_answer(query, results)
        
        return {
            'answer': answer,
            'query_type': 'simple',
            'original_query': query,
            'intent_analysis': None,
            'sub_queries': [{'query': query, 'intent': 'simple', 'priority': 1, 'results_count': len(results)}],
            'execution_plan': [0],
            'retrieved_chunks': results,
            'processing_info': {
                'decomposition_used': False,
                'synthesis_used': False,
                'total_sub_queries': 1,
                'total_results': len(results)
            }
        }
    
    def _simple_result_combination(self, results: List[Dict[str, Any]]) -> str:
        """
        简单的结果组合
        
        Args:
            results: 检索结果列表
            
        Returns:
            组合后的答案
        """
        if not results:
            return "抱歉，没有找到相关信息。"
        
        # 提取内容并组合
        contents = []
        for result in results[:5]:  # 最多5个结果
            content = result.get('content', '')
            if content:
                # 限制长度
                content = content[:300].strip()
                if content and content not in contents:
                    contents.append(content)
        
        if contents:
            return "\n\n".join(contents)
        else:
            return "抱歉，没有找到相关信息。"
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        获取处理统计信息
        
        Returns:
            统计信息字典
        """
        return {
            'decomposer_config': self.decomposer.config,
            'executor_config': self.executor.config,
            'synthesizer_config': self.synthesizer.config,
            'processor_config': self.config
        }
    
    def update_config(self, new_config: Dict[str, Any]):
        """
        更新配置
        
        Args:
            new_config: 新配置
        """
        self.config.update(new_config)
        
        # 更新子组件配置
        if 'decomposition_threshold' in new_config:
            self.decomposer.config['decomposition_threshold'] = new_config['decomposition_threshold']
        
        if 'max_sub_queries' in new_config:
            self.decomposer.config['max_sub_queries'] = new_config['max_sub_queries']
        
        logger.info("配置已更新")

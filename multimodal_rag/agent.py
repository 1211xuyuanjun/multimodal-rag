"""
多模态RAG智能体主类

集成文档解析、处理、存储、检索和生成等功能的主要智能体类。
"""

import os
import sys
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# 添加Qwen-Agent到路径
sys.path.append(str(Path(__file__).parent.parent / "Qwen-Agent"))

from qwen_agent.llm.base import BaseChatModel

from .parsers.folder_parser import FolderParser
from .processors.smart_chunker import SmartChunker
from .storage.vector_store import MultimodalVectorStore
from .retrieval.hybrid_retriever import HybridRetriever
from .retrieval.query_optimizer import QueryOptimizer
from .retrieval.intelligent_query_processor import IntelligentQueryProcessor
from .config import DOCUMENT_PROCESSING_CONFIG


class MultimodalRAGAgent:
    """
    多模态RAG智能体

    集成了文档解析、智能分块、向量存储、混合检索、查询优化和答案生成等功能。
    """

    def __init__(
        self,
        llm: Optional[Union[Dict, BaseChatModel]] = None,
        llm_config: Optional[Dict] = None,
        system_message: Optional[str] = None,
        storage_path: Optional[str] = None,
        **kwargs
    ):
        """
        初始化多模态RAG智能体

        Args:
            llm: 语言模型实例或配置
            llm_config: LLM配置字典
            system_message: 系统消息
            storage_path: 存储路径
            **kwargs: 其他参数
        """
        # 设置LLM
        self.llm = llm
        self.llm_config = llm_config or {}

        # 如果提供了llm_config但没有llm实例，尝试创建LLM实例
        if not self.llm and self.llm_config:
            self.llm = self._create_llm_from_config(self.llm_config)

        # 创建多模态LLM实例
        self.multimodal_llm = self._create_multimodal_llm()

        # 设置默认系统消息
        if system_message is None:
            system_message = self._get_default_system_message()
        self.system_message = system_message

        # 初始化存储路径
        self.storage_path = storage_path or "./rag_storage"
        os.makedirs(self.storage_path, exist_ok=True)

        # 初始化各个组件
        self._init_components()
        
    def _get_default_system_message(self) -> str:
        """获取默认系统消息"""
        return """你是一个多模态智能助手，专门处理文档问答任务。你能够：

1. 理解和分析PDF文档中的文本、图片、表格等多模态内容
2. 基于文档内容回答用户问题
3. 提供准确、详细的信息，并引用相关的文档片段
4. 处理复杂的多模态查询，包括文本描述和图像理解

请始终基于提供的文档内容回答问题，如果文档中没有相关信息，请明确说明。"""

    def _create_llm_from_config(self, llm_config: Dict) -> Optional[BaseChatModel]:
        """从配置创建LLM实例"""
        try:
            from qwen_agent.llm import get_chat_model

            model_name = llm_config.get('model', 'qwen-plus')
            api_key = llm_config.get('api_key')

            if not api_key:
                logger.warning("未提供API密钥，无法创建LLM实例")
                return None

            # 创建LLM实例
            llm = get_chat_model({
                'model': model_name,
                'api_key': api_key,
                'model_server': 'dashscope'
            })

            logger.info(f"成功创建LLM实例: {model_name}")
            return llm

        except Exception as e:
            logger.error(f"创建LLM实例失败: {str(e)}")
            return None

    def _create_multimodal_llm(self) -> Optional[BaseChatModel]:
        """创建多模态LLM实例"""
        try:
            from qwen_agent.llm import get_chat_model

            api_key = self.llm_config.get('api_key')
            if not api_key:
                logger.warning("未提供API密钥，无法创建多模态LLM实例")
                return None

            # 创建多模态LLM实例
            multimodal_llm = get_chat_model({
                'model': 'qwen-vl-max',  # 使用qwen-vl-max模型获得更好的图像理解能力
                'api_key': api_key,
                'model_server': 'dashscope'
            })

            logger.info("成功创建多模态LLM实例: qwen-vl-max")
            return multimodal_llm

        except Exception as e:
            logger.error(f"创建多模态LLM实例失败: {str(e)}")
            return None

    def _init_components(self):
        """初始化各个组件"""
        # 文档解析器 - 只使用文件夹解析器
        self.folder_parser = FolderParser()

        # 文档处理器（使用配置文件设置）
        self.chunker = SmartChunker(
            multimodal_llm=self.multimodal_llm,
            enable_image_description=DOCUMENT_PROCESSING_CONFIG.get('enable_image_description', False)
        )

        # 向量存储
        self.vector_store = MultimodalVectorStore(storage_path=self.storage_path)

        # 检索器
        self.retriever = HybridRetriever(vector_store=self.vector_store)

        # 查询优化器（保留原有的，用于回退）
        self.query_optimizer = QueryOptimizer(llm=self.llm)

        # 智能查询处理器（传递多模态LLM）
        self.intelligent_processor = IntelligentQueryProcessor(
            retriever=self.retriever,
            llm=self.llm,
            multimodal_llm=self.multimodal_llm,
            config={
                'enable_decomposition': True,
                'decomposition_threshold': 6.0,
                'max_sub_queries': 5,
                'enable_synthesis': True,
                'fallback_to_simple': True,
            }
        )
        
    def add_documents(self, file_paths: List[str], replace_existing: bool = True) -> Dict[str, Any]:
        """
        添加文档到知识库

        Args:
            file_paths: 文档文件路径列表（支持PDF文件和包含MD+images的文件夹）
            replace_existing: 是否替换已存在的文档

        Returns:
            处理结果字典
        """
        results = {
            "success": [],
            "failed": [],
            "total_chunks": 0,
            "replaced": [],
            "added": []
        }

        for file_path in file_paths:
            try:
                # 检查文档是否已存在
                existing_info = self.vector_store.get_source_info(file_path)
                if existing_info and replace_existing:
                    logger.info(f"文档已存在，将替换: {file_path}")
                    # 删除已存在的文档数据
                    self.vector_store.delete_by_source(file_path)
                    results["replaced"].append(file_path)
                elif existing_info and not replace_existing:
                    logger.info(f"文档已存在，跳过: {file_path}")
                    continue
                else:
                    results["added"].append(file_path)

                # 解析文档（支持PDF文件和文件夹）
                parsed_doc = self._parse_document(file_path)

                if not parsed_doc:
                    raise Exception(f"文档解析失败: {file_path}")

                # 智能分块
                chunks = self.chunker.chunk_document(parsed_doc)

                # 存储到向量数据库
                self.vector_store.add_chunks(chunks, source=file_path)

                results["success"].append(file_path)
                results["total_chunks"] += len(chunks)

                logger.info(f"成功处理文档: {file_path}, 生成 {len(chunks)} 个块")

            except Exception as e:
                logger.error(f"处理文档失败 {file_path}: {str(e)}")
                results["failed"].append({
                    "file": file_path,
                    "error": str(e)
                })

        return results

    def _parse_document(self, file_path: str):
        """
        解析文档（支持PDF文件和文件夹）

        Args:
            file_path: 文件或文件夹路径

        Returns:
            解析后的文档对象
        """
        import os

        if os.path.isdir(file_path):
            # 文件夹输入，使用文件夹解析器
            logger.info(f"检测到文件夹输入，使用文件夹解析器: {file_path}")
            return self.folder_parser.parse_folder(file_path)
        else:
            # 不支持的文件类型
            logger.warning(f"不支持的文件类型，请提供包含MD文件和图片的文件夹: {file_path}")
            return None

    def query(self, question: str, use_intelligent_processing: bool = True, **kwargs) -> str:
        """
        查询文档并生成回答

        Args:
            question: 用户问题
            use_intelligent_processing: 是否使用智能查询处理（分解、多步执行、汇总）
            **kwargs: 其他参数

        Returns:
            生成的回答
        """
        try:
            if use_intelligent_processing:
                # 使用智能查询处理器
                result = self.intelligent_processor.process_query(question, **kwargs)
                return result['answer']
            else:
                # 使用原有的简单查询流程
                return self._simple_query(question, **kwargs)

        except Exception as e:
            logger.error(f"查询失败: {str(e)}")
            # 回退到简单查询
            try:
                return self._simple_query(question, **kwargs)
            except Exception as fallback_e:
                return f"查询过程中出现错误: {str(e)}。回退查询也失败: {str(fallback_e)}"

    def query_detailed(self, question: str, use_intelligent_processing: bool = True, **kwargs) -> Dict[str, Any]:
        """
        查询文档并返回详细结果

        Args:
            question: 用户问题
            use_intelligent_processing: 是否使用智能查询处理
            **kwargs: 其他参数

        Returns:
            详细的查询结果，包含答案、分解信息、检索结果等
        """
        try:
            if use_intelligent_processing:
                return self.intelligent_processor.process_query(question, **kwargs)
            else:
                # 简单查询的详细结果
                answer = self._simple_query(question, **kwargs)
                return {
                    'answer': answer,
                    'query_type': 'simple_legacy',
                    'original_query': question,
                    'processing_info': {
                        'intelligent_processing_used': False
                    }
                }
        except Exception as e:
            logger.error(f"详细查询失败: {str(e)}")
            return {
                'answer': f"查询过程中出现错误: {str(e)}",
                'query_type': 'error',
                'original_query': question,
                'processing_info': {
                    'error': str(e)
                }
            }

    def _simple_query(self, question: str, **kwargs) -> str:
        """
        简单查询流程（原有逻辑）

        Args:
            question: 用户问题
            **kwargs: 其他参数

        Returns:
            生成的回答
        """
        # 查询优化
        optimized_queries = self.query_optimizer.optimize_query(question)

        # 混合检索
        retrieved_chunks = []
        for query in optimized_queries:
            chunks = self.retriever.retrieve(query, **kwargs)
            retrieved_chunks.extend(chunks)

        # 去重和重排序
        retrieved_chunks = self.retriever.rerank(question, retrieved_chunks)

        # 生成回答
        if not retrieved_chunks:
            return "抱歉，没有找到相关信息来回答您的问题。请尝试重新表述您的问题或提供更多上下文。"

        # 构建上下文
        context_parts = []
        for i, chunk in enumerate(retrieved_chunks[:5]):  # 限制为前5个最相关的结果
            content = chunk.get('content', '').strip()
            if content:
                context_parts.append(f"参考资料{i+1}：{content}")

        context = "\n\n".join(context_parts)

        # 使用LLM生成回答
        prompt = f"""基于以下参考资料回答问题：

{context}

问题：{question}

请基于上述参考资料提供准确、详细的回答。如果参考资料中没有足够信息，请明确说明。"""

        try:
            from qwen_agent.llm.schema import Message, USER, ASSISTANT
            messages = [Message(USER, prompt)]

            response = None
            for response in self.llm.chat(messages):
                continue

            if response and response[-1].role == ASSISTANT:
                return response[-1].content.strip()
            else:
                return "抱歉，生成回答时出现问题。"

        except Exception as e:
            logger.error(f"生成回答失败: {str(e)}")
            return f"生成回答时出现错误: {str(e)}"

    def get_storage_info(self) -> Dict[str, Any]:
        """获取存储信息"""
        return self.vector_store.get_info()

    def clear_storage(self):
        """清空存储"""
        self.vector_store.clear()

    def get_processing_config(self) -> Dict[str, Any]:
        """
        获取查询处理配置

        Returns:
            配置信息字典
        """
        return {
            'intelligent_processor': self.intelligent_processor.get_processing_stats(),
            'query_optimizer': self.query_optimizer.config if hasattr(self.query_optimizer, 'config') else {},
            'retriever': self.retriever.config if hasattr(self.retriever, 'config') else {},
        }

    def update_processing_config(self, config: Dict[str, Any]):
        """
        更新查询处理配置

        Args:
            config: 新配置
        """
        if 'intelligent_processor' in config:
            self.intelligent_processor.update_config(config['intelligent_processor'])

        if 'query_optimizer' in config and hasattr(self.query_optimizer, 'config'):
            self.query_optimizer.config.update(config['query_optimizer'])

        if 'retriever' in config and hasattr(self.retriever, 'config'):
            self.retriever.config.update(config['retriever'])

        logger.info("查询处理配置已更新")

    def set_decomposition_threshold(self, threshold: float):
        """
        设置查询分解阈值

        Args:
            threshold: 分解阈值 (0-10)
        """
        self.intelligent_processor.update_config({
            'decomposition_threshold': threshold
        })
        logger.info(f"查询分解阈值已设置为: {threshold}")

    def enable_intelligent_processing(self, enable: bool = True):
        """
        启用或禁用智能查询处理

        Args:
            enable: 是否启用
        """
        self.intelligent_processor.update_config({
            'enable_decomposition': enable,
            'enable_synthesis': enable
        })
        logger.info(f"智能查询处理已{'启用' if enable else '禁用'}")

    def get_query_analysis(self, question: str) -> Dict[str, Any]:
        """
        分析查询但不执行检索

        Args:
            question: 用户问题

        Returns:
            查询分析结果
        """
        try:
            decomposition = self.intelligent_processor.decomposer.analyze_and_decompose(question)

            return {
                'original_query': question,
                'intent_analysis': {
                    'intent_type': decomposition.intent.intent_type,
                    'complexity_score': decomposition.intent.complexity_score,
                    'key_concepts': decomposition.intent.key_concepts,
                    'question_type': decomposition.intent.question_type,
                    'requires_decomposition': decomposition.intent.requires_decomposition,
                    'reasoning': decomposition.intent.reasoning
                },
                'decomposition': {
                    'sub_queries': [
                        {
                            'query': sq.query,
                            'intent': sq.intent,
                            'priority': sq.priority,
                            'depends_on': sq.depends_on,
                            'context_needed': sq.context_needed
                        }
                        for sq in decomposition.sub_queries
                    ],
                    'execution_plan': decomposition.execution_plan
                }
            }
        except Exception as e:
            logger.error(f"查询分析失败: {str(e)}")
            return {
                'original_query': question,
                'error': str(e)
            }

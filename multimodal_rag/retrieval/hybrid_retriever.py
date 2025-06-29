"""
混合检索器

基于Qwen-Agent的检索框架，实现文本+图像的混合检索和智能重排序。
"""

import sys
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging

# 添加Qwen-Agent到路径
sys.path.append(str(Path(__file__).parent.parent.parent / "Qwen-Agent"))

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False

from ..storage.vector_store import MultimodalVectorStore
from ..config import RETRIEVAL_CONFIG
from .reranker import Reranker

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    混合检索器
    
    结合多种检索方法：
    1. BM25关键词检索
    2. 向量语义检索
    3. 多模态检索
    4. 智能重排序
    """
    
    def __init__(
        self,
        vector_store: MultimodalVectorStore,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化混合检索器
        
        Args:
            vector_store: 向量存储
            config: 配置参数
        """
        self.vector_store = vector_store
        self.config = config or RETRIEVAL_CONFIG
        
        # 初始化BM25索引
        self.bm25_text_index = None
        self.bm25_image_index = None
        self.text_chunks = []
        self.image_chunks = []
        
        # 初始化重排序器
        self.reranker = Reranker()
        
        # 构建BM25索引
        self._build_bm25_indexes()
    
    def _build_bm25_indexes(self):
        """构建BM25索引"""
        if not BM25_AVAILABLE:
            logger.warning("BM25不可用，跳过BM25索引构建")
            return
        
        try:
            # 获取所有文本块
            text_metadata = self.vector_store.metadata_store.get_metadata_by_type('text')
            table_metadata = self.vector_store.metadata_store.get_metadata_by_type('table')
            
            self.text_chunks = text_metadata + table_metadata
            
            if self.text_chunks:
                # 构建文本BM25索引
                text_corpus = [self._tokenize_text(chunk['content']) for chunk in self.text_chunks]
                self.bm25_text_index = BM25Okapi(text_corpus)
                logger.info(f"构建文本BM25索引: {len(self.text_chunks)}个文档")
            
            # 获取所有图像块
            self.image_chunks = self.vector_store.metadata_store.get_metadata_by_type('image')
            
            if self.image_chunks:
                # 构建图像BM25索引（基于OCR文本）
                image_corpus = [self._tokenize_text(chunk['content']) for chunk in self.image_chunks]
                self.bm25_image_index = BM25Okapi(image_corpus)
                logger.info(f"构建图像BM25索引: {len(self.image_chunks)}个文档")
        
        except Exception as e:
            logger.error(f"构建BM25索引失败: {str(e)}")
    
    def _tokenize_text(self, text: str) -> List[str]:
        """
        文本分词
        
        Args:
            text: 输入文本
            
        Returns:
            分词结果
        """
        if not text:
            return []
        
        # 简单的分词实现
        import re
        
        # 移除特殊字符，保留中英文和数字
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text.lower())
        
        # 分词
        words = text.split()
        
        # 对中文进行简单处理（可以集成jieba等分词工具）
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        words.extend(chinese_chars)
        
        return [word for word in words if len(word) > 1]
    
    def retrieve(
        self,
        query: str,
        top_k: int = None,
        search_type: str = 'both',
        enable_rerank: bool = True
    ) -> List[Dict[str, Any]]:
        """
        混合检索
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            search_type: 搜索类型 ('text', 'image', 'both')
            enable_rerank: 是否启用重排序
            
        Returns:
            检索结果列表
        """
        if top_k is None:
            top_k = self.config.get('top_k', 10)
        
        logger.info(f"开始混合检索: {query[:50]}...")
        
        # 收集所有检索结果
        all_results = []
        
        # BM25检索
        bm25_results = self._bm25_search(query, top_k * 2, search_type)
        all_results.extend(bm25_results)
        
        # 向量检索
        vector_results = self._vector_search(query, top_k * 2, search_type)
        all_results.extend(vector_results)
        
        # 合并和去重
        merged_results = self._merge_results(all_results)
        
        # 重排序
        if enable_rerank and merged_results:
            rerank_top_k = self.config.get('rerank_top_k', min(top_k * 2, len(merged_results)))
            merged_results = self.reranker.rerank(query, merged_results[:rerank_top_k])
        
        # 返回top_k结果
        final_results = merged_results[:top_k]
        
        logger.info(f"检索完成: 返回{len(final_results)}个结果")
        return final_results
    
    def _bm25_search(self, query: str, top_k: int, search_type: str) -> List[Dict[str, Any]]:
        """BM25检索"""
        if not BM25_AVAILABLE:
            return []
        
        results = []
        query_tokens = self._tokenize_text(query)
        
        if not query_tokens:
            return []
        
        # 文本BM25检索
        if search_type in ['text', 'both'] and self.bm25_text_index:
            try:
                scores = self.bm25_text_index.get_scores(query_tokens)
                
                # 获取top_k结果
                top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
                
                for idx in top_indices:
                    if scores[idx] > 0:  # 只保留有分数的结果
                        chunk = self.text_chunks[idx].copy()
                        chunk['score'] = float(scores[idx])
                        chunk['retrieval_method'] = 'bm25_text'
                        results.append(chunk)
            
            except Exception as e:
                logger.error(f"BM25文本检索失败: {str(e)}")
        
        # 图像BM25检索
        if search_type in ['image', 'both'] and self.bm25_image_index:
            try:
                scores = self.bm25_image_index.get_scores(query_tokens)
                
                # 获取top_k结果
                top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
                
                for idx in top_indices:
                    if scores[idx] > 0:  # 只保留有分数的结果
                        chunk = self.image_chunks[idx].copy()
                        chunk['score'] = float(scores[idx])
                        chunk['retrieval_method'] = 'bm25_image'
                        results.append(chunk)
            
            except Exception as e:
                logger.error(f"BM25图像检索失败: {str(e)}")
        
        return results
    
    def _vector_search(self, query: str, top_k: int, search_type: str) -> List[Dict[str, Any]]:
        """向量检索"""
        try:
            results = self.vector_store.search(
                query=query,
                top_k=top_k,
                search_type=search_type,
                score_threshold=self.config.get('score_threshold', 0.0)
            )
            
            # 添加检索方法标记
            for result in results:
                if result.get('index_type') == 'text':
                    result['retrieval_method'] = 'vector_text'
                else:
                    result['retrieval_method'] = 'vector_image'
            
            return results
        
        except Exception as e:
            logger.error(f"向量检索失败: {str(e)}")
            return []
    
    def _merge_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        合并检索结果

        Args:
            results: 原始结果列表

        Returns:
            合并后的结果列表
        """
        # 按内容去重
        seen_content = set()
        merged_results = []

        # 计算综合分数（检索分数 + 优先级分数）
        for result in results:
            retrieval_score = result.get('score', 0)
            priority_score = result.get('priority_score', 0.5)
            content_category = result.get('content_category', 'other')

            # 对参考文献类型的内容降权
            if content_category == 'references':
                priority_score *= 0.3

            # 综合分数 = 检索分数 * 优先级权重
            combined_score = retrieval_score * (0.7 + 0.3 * priority_score)
            result['combined_score'] = combined_score

        # 按综合分数排序
        results.sort(key=lambda x: x.get('combined_score', 0), reverse=True)

        for result in results:
            content = result.get('content', '')
            content_hash = hash(content)

            if content_hash not in seen_content:
                seen_content.add(content_hash)
                merged_results.append(result)

        return merged_results
    
    def rerank(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        重排序结果
        
        Args:
            query: 查询文本
            results: 检索结果
            
        Returns:
            重排序后的结果
        """
        return self.reranker.rerank(query, results)
    
    def update_indexes(self):
        """更新索引"""
        logger.info("更新检索索引")
        self._build_bm25_indexes()
        logger.info("索引更新完成")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {
            'text_chunks': len(self.text_chunks),
            'image_chunks': len(self.image_chunks),
            'bm25_text_available': self.bm25_text_index is not None,
            'bm25_image_available': self.bm25_image_index is not None,
            'vector_store_info': self.vector_store.get_info()
        }
        
        return stats

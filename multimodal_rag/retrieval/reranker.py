"""
重排序器

对检索结果进行智能重排序，提升相关性。
"""

import re
import math
from typing import List, Dict, Any, Optional
import logging

try:
    from sentence_transformers import SentenceTransformer, util
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)


class Reranker:
    """
    重排序器
    
    使用多种策略对检索结果进行重排序：
    1. 语义相似度重排序
    2. 关键词匹配度
    3. 内容类型权重
    4. 位置信息
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化重排序器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        
        # 初始化重排序模型
        self.rerank_model = None
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                # 使用专门的重排序模型
                self.rerank_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
                logger.info("重排序模型初始化成功")
            except Exception as e:
                logger.error(f"重排序模型初始化失败: {str(e)}")
        
        # 权重配置
        self.weights = {
            'semantic_similarity': 0.4,
            'keyword_match': 0.3,
            'content_type': 0.2,
            'position_score': 0.1
        }
        
        # 内容类型权重
        self.content_type_weights = {
            'text': 1.0,
            'table': 0.9,
            'image': 0.8
        }
    
    def rerank(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        重排序检索结果
        
        Args:
            query: 查询文本
            results: 检索结果列表
            
        Returns:
            重排序后的结果列表
        """
        if not results:
            return results
        
        logger.info(f"开始重排序{len(results)}个结果")
        
        # 计算各种分数
        semantic_scores = self._calculate_semantic_scores(query, results)
        keyword_scores = self._calculate_keyword_scores(query, results)
        content_type_scores = self._calculate_content_type_scores(results)
        position_scores = self._calculate_position_scores(results)
        
        # 计算综合分数
        for i, result in enumerate(results):
            combined_score = (
                semantic_scores[i] * self.weights['semantic_similarity'] +
                keyword_scores[i] * self.weights['keyword_match'] +
                content_type_scores[i] * self.weights['content_type'] +
                position_scores[i] * self.weights['position_score']
            )
            
            result['rerank_score'] = combined_score
            result['semantic_score'] = semantic_scores[i]
            result['keyword_score'] = keyword_scores[i]
            result['content_type_score'] = content_type_scores[i]
            result['position_score'] = position_scores[i]
        
        # 按综合分数排序
        results.sort(key=lambda x: x['rerank_score'], reverse=True)
        
        logger.info("重排序完成")
        return results
    
    def _calculate_semantic_scores(self, query: str, results: List[Dict[str, Any]]) -> List[float]:
        """计算语义相似度分数"""
        if not self.rerank_model:
            # 如果没有重排序模型，使用原始分数
            return [result.get('score', 0.0) for result in results]
        
        try:
            # 提取内容
            contents = [result.get('content', '') for result in results]
            
            # 计算语义相似度
            query_embedding = self.rerank_model.encode([query])
            content_embeddings = self.rerank_model.encode(contents)
            
            # 计算余弦相似度
            similarities = util.cos_sim(query_embedding, content_embeddings)[0]
            
            return [float(sim) for sim in similarities]
        
        except Exception as e:
            logger.error(f"计算语义相似度失败: {str(e)}")
            return [result.get('score', 0.0) for result in results]
    
    def _calculate_keyword_scores(self, query: str, results: List[Dict[str, Any]]) -> List[float]:
        """计算关键词匹配分数"""
        query_keywords = self._extract_keywords(query)
        
        scores = []
        for result in results:
            content = result.get('content', '')
            content_keywords = self._extract_keywords(content)
            
            # 计算关键词重叠度
            if not query_keywords:
                score = 0.0
            else:
                overlap = len(set(query_keywords) & set(content_keywords))
                score = overlap / len(query_keywords)
            
            # 考虑关键词在内容中的位置和频率
            position_bonus = self._calculate_keyword_position_bonus(query_keywords, content)
            frequency_bonus = self._calculate_keyword_frequency_bonus(query_keywords, content)
            
            final_score = score + position_bonus * 0.2 + frequency_bonus * 0.1
            scores.append(min(final_score, 1.0))  # 限制在[0,1]范围内
        
        return scores
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        if not text:
            return []
        
        # 简单的关键词提取
        text = text.lower()
        
        # 移除标点符号
        text = re.sub(r'[^\w\s\u4e00-\u9fff]', ' ', text)
        
        # 分词
        words = text.split()
        
        # 过滤停用词和短词
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
        keywords = [word for word in words if len(word) > 1 and word not in stop_words]
        
        # 提取中文字符
        chinese_chars = re.findall(r'[\u4e00-\u9fff]+', text)
        keywords.extend(chinese_chars)
        
        return list(set(keywords))
    
    def _calculate_keyword_position_bonus(self, keywords: List[str], content: str) -> float:
        """计算关键词位置奖励"""
        if not keywords or not content:
            return 0.0
        
        content_lower = content.lower()
        total_bonus = 0.0
        
        for keyword in keywords:
            pos = content_lower.find(keyword.lower())
            if pos != -1:
                # 越靠前的关键词获得更高奖励
                position_ratio = 1 - (pos / len(content))
                total_bonus += position_ratio
        
        return total_bonus / len(keywords) if keywords else 0.0
    
    def _calculate_keyword_frequency_bonus(self, keywords: List[str], content: str) -> float:
        """计算关键词频率奖励"""
        if not keywords or not content:
            return 0.0
        
        content_lower = content.lower()
        total_frequency = 0
        
        for keyword in keywords:
            frequency = content_lower.count(keyword.lower())
            # 使用对数函数避免频率过高的词获得过多奖励
            total_frequency += math.log(1 + frequency)
        
        return min(total_frequency / len(keywords), 1.0) if keywords else 0.0
    
    def _calculate_content_type_scores(self, results: List[Dict[str, Any]]) -> List[float]:
        """计算内容类型分数"""
        scores = []
        
        for result in results:
            content_type = result.get('chunk_type', 'text')
            weight = self.content_type_weights.get(content_type, 0.5)
            scores.append(weight)
        
        return scores
    
    def _calculate_position_scores(self, results: List[Dict[str, Any]]) -> List[float]:
        """计算位置分数"""
        scores = []
        
        for result in results:
            # 基于页码和块索引计算位置分数
            page_num = result.get('page_num', 1)
            chunk_index = result.get('chunk_index', 0)
            
            # 越靠前的页面和块获得更高分数
            page_score = 1.0 / (1 + math.log(page_num))
            chunk_score = 1.0 / (1 + chunk_index * 0.1)
            
            position_score = (page_score + chunk_score) / 2
            scores.append(position_score)
        
        return scores
    
    def _normalize_scores(self, scores: List[float]) -> List[float]:
        """标准化分数到[0,1]范围"""
        if not scores:
            return scores
        
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            return [1.0] * len(scores)
        
        return [(score - min_score) / (max_score - min_score) for score in scores]

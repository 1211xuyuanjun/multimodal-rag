"""
配置文件

包含系统的各种配置参数。
"""

import os
from typing import Dict, Any

# 基础配置
DEFAULT_STORAGE_PATH = "./rag_storage"
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50
DEFAULT_MAX_CHUNKS = 10

# LLM配置
DEFAULT_LLM_CONFIG = {
    "model": "qwen-plus",
    "temperature": 0.1,
    "max_tokens": 2000,
}

# 多模态模型配置
MULTIMODAL_MODEL_CONFIG = {
    "vision_model": "qwen-vl-max",  # 使用qwen-vl-max模型获得更好的图像理解能力
    "embedding_model": "text-embedding-v1",
    "clip_model": "ViT-B/32",
    "enable_image_analysis": False,  # 默认禁用耗时的图像分析
    "enable_simple_description": True,  # 启用简化的图像描述
    "image_description_prompt": "请详细描述这张图片的内容，包括：1. 主要对象和场景；2. 图片中的文字内容；3. 图表、表格或技术图形的具体信息；4. 颜色、布局等视觉特征。请用中文回答，内容要准确详细。",
}

# 文档处理配置
DOCUMENT_PROCESSING_CONFIG = {
    "enable_text_chunking": True,  # 启用文本分块
    "skip_reference_sections": True,  # 跳过参考文献部分
    "enable_image_description": True,  # 启用图像描述生成

    "max_image_description_length": 500,  # 图像描述最大长度
    "prefer_alt_text": False,  # 优先使用LLM生成的描述
    "show_image_description_in_console": True,  # 在控制台显示图片描述
}







# 向量存储配置
VECTOR_STORE_CONFIG = {
    "embedding_dim": 1536,
    "index_type": "HNSW",  # 可选: "Flat", "IVF", "HNSW"
    "metric": "cosine",
    "nlist": 100,  # IVF索引的聚类数量
    "m": 16,  # HNSW索引的连接数
    "ef_construction": 200,  # HNSW构建时的搜索参数
    "ef_search": 100,  # HNSW搜索时的参数
}

# 检索配置
RETRIEVAL_CONFIG = {
    "top_k": 10,
    "score_threshold": 0.7,
    "rerank_top_k": 5,
    "hybrid_weights": {
        "bm25": 0.3,
        "vector": 0.5,
        "multimodal": 0.2,
    }
}

# 查询优化配置
QUERY_OPTIMIZATION_CONFIG = {
    "enable_query_expansion": True,
    "enable_query_rewrite": True,
    "enable_self_critique": True,
    "enable_llm_diversification": True,  # 新增：启用LLM多样化查询生成
    "max_expansions": 3,
    "expansion_methods": ["synonym", "related_terms", "context"],
    "similarity_threshold": 0.7,  # 新增：查询相似度阈值
}

# 生成配置
GENERATION_CONFIG = {
    "max_context_length": 12000,  # 增加上下文长度
    "answer_max_length": 2000,    # 增加答案最大长度
    "include_sources": True,
    "citation_format": "markdown",
    "min_chunk_length": 50,       # 最小块长度
    "context_overlap": 0.1,       # 上下文重叠比例
}

# 日志配置
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "multimodal_rag.log",
}

# 缓存配置
CACHE_CONFIG = {
    "enable_cache": True,
    "cache_dir": "./cache",
    "max_cache_size": "1GB",
    "cache_ttl": 3600,  # 缓存过期时间(秒)
}


def get_config() -> Dict[str, Any]:
    """获取完整配置"""
    return {
        "storage_path": os.getenv("RAG_STORAGE_PATH", DEFAULT_STORAGE_PATH),
        "chunk_size": int(os.getenv("RAG_CHUNK_SIZE", DEFAULT_CHUNK_SIZE)),
        "chunk_overlap": int(os.getenv("RAG_CHUNK_OVERLAP", DEFAULT_CHUNK_OVERLAP)),
        "max_chunks": int(os.getenv("RAG_MAX_CHUNKS", DEFAULT_MAX_CHUNKS)),
        "llm": DEFAULT_LLM_CONFIG,
        "multimodal": MULTIMODAL_MODEL_CONFIG,

        "vector_store": VECTOR_STORE_CONFIG,
        "retrieval": RETRIEVAL_CONFIG,
        "query_optimization": QUERY_OPTIMIZATION_CONFIG,
        "generation": GENERATION_CONFIG,
        "logging": LOGGING_CONFIG,
        "cache": CACHE_CONFIG,
    }


def update_config_from_env():
    """从环境变量更新配置"""
    # API Keys
    if os.getenv("DASHSCOPE_API_KEY"):
        DEFAULT_LLM_CONFIG["api_key"] = os.getenv("DASHSCOPE_API_KEY")
        MULTIMODAL_MODEL_CONFIG["api_key"] = os.getenv("DASHSCOPE_API_KEY")
    
    if os.getenv("OPENAI_API_KEY"):
        DEFAULT_LLM_CONFIG["openai_api_key"] = os.getenv("OPENAI_API_KEY")
    
    # 其他环境变量配置
    if os.getenv("RAG_ENABLE_GPU"):
        VECTOR_STORE_CONFIG["use_gpu"] = os.getenv("RAG_ENABLE_GPU").lower() == "true"


# 初始化时更新配置
update_config_from_env()

#!/usr/bin/env python3
"""
重建向量索引的脚本

该脚本会：
1. 读取更新后的图像数据
2. 重新生成向量embeddings
3. 重建向量索引
"""

import os
import sys
import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from multimodal_rag.storage.vector_store import MultimodalVectorStore
from multimodal_rag.storage.metadata_store import MetadataStore
from multimodal_rag.processors.smart_chunker import DocumentChunk

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorIndexRebuilder:
    """向量索引重建器"""
    
    def __init__(self, storage_path: str = "./webui_storage"):
        self.storage_path = storage_path
        self.db_path = os.path.join(storage_path, "metadata", "metadata.db")
        
        # 初始化存储组件
        self.metadata_store = MetadataStore(os.path.join(storage_path, "metadata"))
        self.vector_store = MultimodalVectorStore(storage_path)
    
    def get_all_chunks(self) -> List[DocumentChunk]:
        """获取所有文档块"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT content, chunk_type, metadata_json 
                FROM metadata 
                ORDER BY page_num, chunk_index
            ''')
            
            chunks = []
            for row in cursor.fetchall():
                content, chunk_type, metadata_json = row
                metadata = json.loads(metadata_json)
                
                # 创建DocumentChunk对象
                chunk = DocumentChunk(
                    content=content,
                    chunk_type=chunk_type,
                    metadata=metadata,
                    token_count=metadata.get('token_count', 0)
                )
                chunks.append(chunk)
            
            conn.close()
            logger.info(f"获取到 {len(chunks)} 个文档块")
            return chunks
            
        except Exception as e:
            logger.error(f"获取文档块失败: {str(e)}")
            return []
    
    def clear_existing_indexes(self):
        """清空现有索引"""
        try:
            # 删除索引文件
            index_files = [
                os.path.join(self.storage_path, "text_index.faiss"),
                os.path.join(self.storage_path, "image_index.faiss")
            ]
            
            for index_file in index_files:
                if os.path.exists(index_file):
                    os.remove(index_file)
                    logger.info(f"删除索引文件: {index_file}")
            
            # 重新初始化向量存储
            self.vector_store = MultimodalVectorStore(self.storage_path)
            logger.info("向量存储重新初始化完成")
            
        except Exception as e:
            logger.error(f"清空索引失败: {str(e)}")
    
    def rebuild_indexes(self):
        """重建向量索引"""
        try:
            # 获取所有文档块
            chunks = self.get_all_chunks()
            if not chunks:
                logger.error("没有找到文档块，无法重建索引")
                return
            
            # 清空现有索引
            self.clear_existing_indexes()
            
            # 按来源分组
            chunks_by_source = {}
            for chunk in chunks:
                source = chunk.metadata.get('source', 'unknown')
                if source not in chunks_by_source:
                    chunks_by_source[source] = []
                chunks_by_source[source].append(chunk)
            
            # 重新添加所有块
            total_added = 0
            for source, source_chunks in chunks_by_source.items():
                logger.info(f"重建索引: {source} ({len(source_chunks)} 个块)")
                self.vector_store.add_chunks(source_chunks, source)
                total_added += len(source_chunks)
            
            logger.info(f"向量索引重建完成: 总共处理 {total_added} 个文档块")
            
        except Exception as e:
            logger.error(f"重建索引失败: {str(e)}")
    
    def test_search(self):
        """测试搜索功能"""
        try:
            # 测试图像搜索
            logger.info("测试图像搜索...")
            results = self.vector_store.search(
                query="第一张图片",
                top_k=5,
                search_type="image"
            )
            
            logger.info(f"图像搜索结果: {len(results)} 个")
            for i, result in enumerate(results[:3]):
                logger.info(f"结果 {i+1}: {result.get('content', '')[:100]}...")
            
            # 测试文本搜索
            logger.info("测试文本搜索...")
            results = self.vector_store.search(
                query="公式",
                top_k=5,
                search_type="both"
            )
            
            logger.info(f"综合搜索结果: {len(results)} 个")
            for i, result in enumerate(results[:3]):
                logger.info(f"结果 {i+1}: {result.get('content', '')[:100]}...")
            
        except Exception as e:
            logger.error(f"测试搜索失败: {str(e)}")

def main():
    """主函数"""
    print("🔄 向量索引重建工具")
    print("=" * 50)
    
    rebuilder = VectorIndexRebuilder()
    
    print("🚀 开始重建向量索引...")
    rebuilder.rebuild_indexes()
    
    print("🧪 测试搜索功能...")
    rebuilder.test_search()
    
    print("✅ 处理完成！")

if __name__ == "__main__":
    main()

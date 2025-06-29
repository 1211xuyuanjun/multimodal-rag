#!/usr/bin/env python3
"""
存储清理和管理工具

该脚本用于：
1. 分析当前存储状态
2. 清理重复或无效数据
3. 重新组织存储结构
4. 验证数据一致性
"""

import os
import sys
import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from multimodal_rag.storage.vector_store import MultimodalVectorStore
from multimodal_rag.storage.metadata_store import MetadataStore

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StorageManager:
    """存储管理器"""
    
    def __init__(self, storage_path: str = "./webui_storage"):
        self.storage_path = storage_path
        self.db_path = os.path.join(storage_path, "metadata", "metadata.db")
        
        # 初始化存储组件
        self.metadata_store = MetadataStore(os.path.join(storage_path, "metadata"))
        self.vector_store = MultimodalVectorStore(storage_path)
    
    def analyze_storage(self) -> Dict[str, Any]:
        """分析存储状态"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 总体统计
            cursor.execute('SELECT COUNT(*) FROM metadata')
            total_count = cursor.fetchone()[0]
            
            # 按类型统计
            cursor.execute('SELECT chunk_type, COUNT(*) FROM metadata GROUP BY chunk_type')
            type_stats = dict(cursor.fetchall())
            
            # 按来源统计
            cursor.execute('SELECT source, COUNT(*) FROM metadata GROUP BY source')
            source_stats = dict(cursor.fetchall())
            
            # 检查重复内容
            cursor.execute('''
                SELECT content, COUNT(*) as count 
                FROM metadata 
                GROUP BY content 
                HAVING count > 1
                ORDER BY count DESC
            ''')
            duplicates = cursor.fetchall()
            
            conn.close()
            
            analysis = {
                'total_records': total_count,
                'type_distribution': type_stats,
                'source_distribution': source_stats,
                'duplicate_content_count': len(duplicates),
                'top_duplicates': duplicates[:10] if duplicates else []
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"分析存储失败: {str(e)}")
            return {}
    
    def print_analysis(self, analysis: Dict[str, Any]):
        """打印分析结果"""
        print("📊 存储状态分析")
        print("=" * 50)
        
        print(f"📈 总记录数: {analysis.get('total_records', 0)}")
        
        print("\n📋 类型分布:")
        for chunk_type, count in analysis.get('type_distribution', {}).items():
            print(f"  {chunk_type}: {count}")
        
        print("\n📁 来源分布:")
        for source, count in analysis.get('source_distribution', {}).items():
            source_name = os.path.basename(source) if source else "未知"
            print(f"  {source_name}: {count}")
        
        if analysis.get('duplicate_content_count', 0) > 0:
            print(f"\n⚠️  发现 {analysis['duplicate_content_count']} 组重复内容")
            print("前10个重复内容:")
            for content, count in analysis.get('top_duplicates', []):
                print(f"  重复{count}次: {content[:50]}...")
    
    def clean_duplicates(self) -> int:
        """清理重复数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 查找重复记录
            cursor.execute('''
                SELECT content, MIN(rowid) as keep_id, COUNT(*) as count
                FROM metadata 
                GROUP BY content 
                HAVING count > 1
            ''')
            
            duplicates = cursor.fetchall()
            total_removed = 0
            
            for content, keep_id, count in duplicates:
                # 删除除了最早记录之外的所有重复记录
                cursor.execute('''
                    DELETE FROM metadata 
                    WHERE content = ? AND rowid != ?
                ''', (content, keep_id))
                
                removed = cursor.rowcount
                total_removed += removed
                logger.info(f"删除了 {removed} 个重复记录: {content[:50]}...")
            
            conn.commit()
            conn.close()
            
            logger.info(f"总共删除了 {total_removed} 个重复记录")
            return total_removed
            
        except Exception as e:
            logger.error(f"清理重复数据失败: {str(e)}")
            return 0
    
    def clean_by_source(self, source_pattern: str = None):
        """按来源清理数据"""
        try:
            analysis = self.analyze_storage()
            sources = list(analysis.get('source_distribution', {}).keys())
            
            if not sources:
                print("没有找到任何数据源")
                return
            
            print("\n📁 当前数据源:")
            for i, source in enumerate(sources):
                source_name = os.path.basename(source) if source else "未知"
                count = analysis['source_distribution'][source]
                print(f"  {i+1}. {source_name} ({count} 条记录)")
            
            if source_pattern:
                # 自动清理匹配的来源
                to_remove = [s for s in sources if source_pattern in s]
            else:
                # 交互式选择
                print("\n请选择要删除的数据源 (输入编号，多个用逗号分隔，或输入 'all' 清空所有):")
                choice = input().strip()
                
                if choice.lower() == 'all':
                    to_remove = sources
                else:
                    try:
                        indices = [int(x.strip()) - 1 for x in choice.split(',')]
                        to_remove = [sources[i] for i in indices if 0 <= i < len(sources)]
                    except:
                        print("无效输入")
                        return
            
            # 删除选中的来源
            for source in to_remove:
                source_name = os.path.basename(source) if source else "未知"
                print(f"🗑️  删除数据源: {source_name}")
                self.vector_store.delete_by_source(source)
            
            if to_remove:
                print("✅ 数据源删除完成，建议重建向量索引")
                
        except Exception as e:
            logger.error(f"按来源清理失败: {str(e)}")
    
    def rebuild_indexes(self):
        """重建向量索引"""
        try:
            print("🔄 重建向量索引...")
            
            # 获取所有数据
            all_metadata = self.metadata_store.get_all_metadata()
            if not all_metadata:
                print("没有数据需要重建索引")
                return
            
            # 清空现有索引
            self.vector_store.clear()
            
            # 按来源分组重建
            sources = set(m.get('source') for m in all_metadata)
            
            for source in sources:
                if not source:
                    continue
                    
                source_data = [m for m in all_metadata if m.get('source') == source]
                print(f"重建索引: {os.path.basename(source)} ({len(source_data)} 条记录)")
                
                # 这里需要重新创建DocumentChunk对象
                from multimodal_rag.processors.smart_chunker import DocumentChunk
                
                chunks = []
                for metadata in source_data:
                    chunk = DocumentChunk(
                        content=metadata.get('content', ''),
                        chunk_type=metadata.get('chunk_type', 'text'),
                        metadata=metadata,
                        token_count=metadata.get('token_count', 0)
                    )
                    chunks.append(chunk)
                
                self.vector_store.add_chunks(chunks, source)
            
            print("✅ 向量索引重建完成")
            
        except Exception as e:
            logger.error(f"重建索引失败: {str(e)}")
    
    def validate_storage(self) -> bool:
        """验证存储一致性"""
        try:
            print("🔍 验证存储一致性...")
            
            # 检查文件是否存在
            required_files = [
                os.path.join(self.storage_path, "text_index.faiss"),
                os.path.join(self.storage_path, "image_index.faiss"),
                self.db_path
            ]
            
            missing_files = [f for f in required_files if not os.path.exists(f)]
            if missing_files:
                print(f"❌ 缺少文件: {missing_files}")
                return False
            
            # 检查数据库完整性
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()[0]
            conn.close()
            
            if result != "ok":
                print(f"❌ 数据库完整性检查失败: {result}")
                return False
            
            print("✅ 存储验证通过")
            return True
            
        except Exception as e:
            logger.error(f"验证存储失败: {str(e)}")
            return False

def main():
    """主函数"""
    print("🧹 存储清理和管理工具")
    print("=" * 50)
    
    manager = StorageManager()
    
    # 分析当前状态
    analysis = manager.analyze_storage()
    manager.print_analysis(analysis)
    
    if analysis.get('total_records', 0) == 0:
        print("\n📭 存储为空，无需清理")
        return
    
    print("\n🛠️  可用操作:")
    print("1. 清理重复数据")
    print("2. 按来源管理数据")
    print("3. 重建向量索引")
    print("4. 验证存储一致性")
    print("5. 完全清空存储")
    print("0. 退出")
    
    while True:
        choice = input("\n请选择操作 (0-5): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            removed = manager.clean_duplicates()
            if removed > 0:
                print(f"✅ 清理了 {removed} 个重复记录")
        elif choice == "2":
            manager.clean_by_source()
        elif choice == "3":
            manager.rebuild_indexes()
        elif choice == "4":
            manager.validate_storage()
        elif choice == "5":
            confirm = input("确认要清空所有存储吗？(yes/no): ").strip().lower()
            if confirm == "yes":
                manager.vector_store.clear()
                print("✅ 存储已清空")
        else:
            print("无效选择，请重试")

if __name__ == "__main__":
    main()

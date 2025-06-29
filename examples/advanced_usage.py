"""
高级使用示例

演示多模态RAG系统的高级功能，包括自定义配置、批量处理等。
"""

import os
import sys
from pathlib import Path
import json

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from multimodal_rag import MultimodalRAGAgent
from multimodal_rag.config import get_config


def advanced_configuration_example():
    """高级配置示例"""
    print("=== 高级配置示例 ===\n")
    
    # 自定义配置
    custom_config = get_config()
    
    # 修改配置参数
    custom_config['chunk_size'] = 300  # 较小的块大小
    custom_config['chunk_overlap'] = 30  # 较小的重叠
    custom_config['pdf_parser']['extract_images'] = True  # 启用图片提取
    custom_config['ocr']['engine'] = 'easyocr'  # 使用EasyOCR
    custom_config['retrieval']['top_k'] = 15  # 增加检索结果数量
    
    print("自定义配置:")
    print(json.dumps(custom_config, indent=2, ensure_ascii=False))
    
    # 使用自定义配置创建智能体
    agent = MultimodalRAGAgent(
        llm_config={
            "model": "qwen-plus",
            "api_key": os.getenv("DASHSCOPE_API_KEY"),
            "temperature": 0.1
        },
        storage_path="./advanced_storage"
    )
    
    print("\n✓ 使用自定义配置的智能体创建完成")
    return agent


def batch_processing_example(agent):
    """批量处理示例"""
    print("\n=== 批量处理示例 ===\n")
    
    # 批量添加文档
    document_folder = "./documents"  # 假设的文档文件夹
    
    if os.path.exists(document_folder):
        pdf_files = []
        for file in os.listdir(document_folder):
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(document_folder, file))
        
        if pdf_files:
            print(f"发现 {len(pdf_files)} 个PDF文件")
            
            # 批量处理
            for i, pdf_file in enumerate(pdf_files, 1):
                print(f"处理文件 {i}/{len(pdf_files)}: {os.path.basename(pdf_file)}")
                
                try:
                    result = agent.add_documents([pdf_file])
                    print(f"  ✓ 成功，生成 {result['total_chunks']} 个块")
                except Exception as e:
                    print(f"  ✗ 失败: {str(e)}")
        else:
            print("文档文件夹中没有PDF文件")
    else:
        print(f"文档文件夹不存在: {document_folder}")
        print("创建模拟批量处理结果...")
        
        # 模拟批量处理
        mock_files = ["doc1.pdf", "doc2.pdf", "doc3.pdf"]
        for i, filename in enumerate(mock_files, 1):
            print(f"模拟处理文件 {i}/{len(mock_files)}: {filename}")
            print(f"  ✓ 模拟成功，生成 {10 + i * 5} 个块")


def multi_query_example(agent):
    """多查询示例"""
    print("\n=== 多查询示例 ===\n")
    
    # 不同类型的查询
    query_examples = {
        "总结类": [
            "请总结所有文档的主要内容",
            "文档的核心观点是什么？",
            "请概括文档的关键信息"
        ],
        "分析类": [
            "文档中提到了哪些重要数据？",
            "有哪些趋势和模式？",
            "文档的结论是什么？"
        ],
        "查找类": [
            "文档中有哪些图表？",
            "提到了哪些具体的案例？",
            "有哪些重要的时间节点？"
        ],
        "比较类": [
            "不同章节的内容有什么区别？",
            "前后观点是否一致？",
            "有哪些对比数据？"
        ]
    }
    
    for category, queries in query_examples.items():
        print(f"\n{category}查询:")
        print("-" * 30)
        
        for i, query in enumerate(queries, 1):
            print(f"\n{i}. {query}")
            
            try:
                # 这里可以添加真实的查询逻辑
                print("   [模拟回答] 基于文档内容的详细回答...")
            except Exception as e:
                print(f"   查询失败: {str(e)}")


def performance_analysis_example(agent):
    """性能分析示例"""
    print("\n=== 性能分析示例 ===\n")
    
    # 获取存储统计信息
    storage_info = agent.get_storage_info()
    
    print("存储统计:")
    print(f"  - 文本块: {storage_info.get('text_count', 0)}")
    print(f"  - 图像块: {storage_info.get('image_count', 0)}")
    print(f"  - 总计: {storage_info.get('total_count', 0)}")
    
    # 模拟检索性能测试
    print("\n检索性能测试:")
    test_queries = [
        "简单查询",
        "复杂的多关键词查询包含专业术语",
        "图片相关的查询内容"
    ]
    
    for query in test_queries:
        print(f"\n测试查询: {query}")
        print("  [模拟] 检索时间: 0.5秒")
        print("  [模拟] 返回结果: 8个相关块")
        print("  [模拟] 平均相关性: 0.85")


def export_results_example(agent):
    """导出结果示例"""
    print("\n=== 导出结果示例 ===\n")
    
    # 模拟导出功能
    export_data = {
        "system_info": {
            "version": "1.0.0",
            "timestamp": "2024-01-01T00:00:00Z"
        },
        "storage_stats": agent.get_storage_info(),
        "sample_queries": [
            {
                "query": "文档总结",
                "answer": "这是一个示例回答...",
                "sources": ["doc1.pdf", "doc2.pdf"]
            }
        ]
    }
    
    # 保存到文件
    export_file = "rag_results.json"
    try:
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        print(f"✓ 结果已导出到: {export_file}")
    except Exception as e:
        print(f"✗ 导出失败: {str(e)}")


def cleanup_example(agent):
    """清理示例"""
    print("\n=== 清理示例 ===\n")
    
    # 获取清理前的信息
    before_info = agent.get_storage_info()
    print(f"清理前: {before_info.get('total_count', 0)} 个块")
    
    # 清理存储（注意：这会删除所有数据）
    print("执行清理操作...")
    # agent.clear_storage()  # 取消注释以执行真实清理
    
    print("✓ 清理完成（模拟）")
    print("清理后: 0 个块")


def main():
    """主函数"""
    print("多模态RAG系统高级使用示例")
    print("=" * 50)
    
    try:
        # 1. 高级配置
        agent = advanced_configuration_example()
        
        # 2. 批量处理
        batch_processing_example(agent)
        
        # 3. 多查询示例
        multi_query_example(agent)
        
        # 4. 性能分析
        performance_analysis_example(agent)
        
        # 5. 导出结果
        export_results_example(agent)
        
        # 6. 清理（可选）
        # cleanup_example(agent)
        
        print("\n" + "=" * 50)
        print("高级示例演示完成")
        
    except Exception as e:
        print(f"示例执行失败: {str(e)}")


if __name__ == "__main__":
    main()

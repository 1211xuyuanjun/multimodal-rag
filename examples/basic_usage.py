"""
基本使用示例

演示多模态RAG系统的基本功能。
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from multimodal_rag import MultimodalRAGAgent


def main():
    """主函数"""
    print("=== 多模态RAG系统基本使用示例 ===\n")
    
    # 1. 初始化智能体
    print("1. 初始化多模态RAG智能体...")
    
    # 配置LLM（需要设置API密钥）
    llm_config = {
        "model": "qwen-plus",
        "api_key": os.getenv("DASHSCOPE_API_KEY"),  # 从环境变量获取API密钥
        "temperature": 0.1,
        "max_tokens": 2000
    }
    
    # 创建智能体
    agent = MultimodalRAGAgent(
        llm_config=llm_config,
        storage_path="./example_storage"
    )
    
    print("✓ 智能体初始化完成\n")
    
    # 2. 添加文档
    print("2. 添加PDF文档到知识库...")
    
    # 示例PDF文件路径（需要用户提供实际的PDF文件）
    pdf_files = [
        # "path/to/your/document1.pdf",
        # "path/to/your/document2.pdf",
    ]
    
    if not pdf_files:
        print("⚠️ 请在pdf_files列表中添加实际的PDF文件路径")
        print("示例：pdf_files = ['./documents/sample.pdf']")
        return
    
    # 添加文档
    results = agent.add_documents(pdf_files)
    
    print(f"✓ 文档添加完成:")
    print(f"  - 成功: {len(results['success'])}个文件")
    print(f"  - 失败: {len(results['failed'])}个文件")
    print(f"  - 总块数: {results['total_chunks']}")
    
    if results['failed']:
        print("失败的文件:")
        for failed in results['failed']:
            print(f"  - {failed['file']}: {failed['error']}")
    
    print()
    
    # 3. 查询示例
    print("3. 进行查询...")
    
    queries = [
        "请总结文档的主要内容",
        "文档中有哪些重要的数据和统计信息？",
        "文档中的图表说明了什么？",
        "请提取文档中的关键要点"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n查询 {i}: {query}")
        print("-" * 50)
        
        try:
            answer = agent.query(query)
            print(f"回答: {answer}")
        except Exception as e:
            print(f"查询失败: {str(e)}")
    
    # 4. 获取存储信息
    print("\n4. 存储信息:")
    print("-" * 50)
    
    storage_info = agent.get_storage_info()
    print(f"存储路径: {storage_info['storage_path']}")
    print(f"文本块数量: {storage_info['text_count']}")
    print(f"图像块数量: {storage_info['image_count']}")
    print(f"总块数量: {storage_info['total_count']}")
    
    print("\n=== 示例完成 ===")


def demo_with_sample_data():
    """使用示例数据的演示"""
    print("=== 使用示例数据的演示 ===\n")
    
    # 创建智能体（不需要真实的LLM）
    agent = MultimodalRAGAgent(
        llm=None,  # 演示模式，不使用真实LLM
        storage_path="./demo_storage"
    )
    
    print("✓ 演示智能体创建完成")
    
    # 模拟添加文档的结果
    print("\n模拟文档添加结果:")
    mock_results = {
        "success": ["demo_document.pdf"],
        "failed": [],
        "total_chunks": 15
    }
    
    print(f"✓ 成功添加: {mock_results['success']}")
    print(f"✓ 生成块数: {mock_results['total_chunks']}")
    
    # 模拟查询
    print("\n模拟查询结果:")
    queries = [
        "文档的主要内容是什么？",
        "有哪些重要数据？"
    ]
    
    for query in queries:
        print(f"\n问题: {query}")
        print("回答: [演示模式] 这是一个模拟回答，展示系统的基本功能。")
    
    print("\n=== 演示完成 ===")


if __name__ == "__main__":
    # 检查是否有API密钥
    if os.getenv("DASHSCOPE_API_KEY"):
        main()
    else:
        print("未检测到DASHSCOPE_API_KEY环境变量")
        print("运行演示模式...\n")
        demo_with_sample_data()

# 多模态智能体RAG系统用户指南

## 目录

1. [系统概述](#系统概述)
2. [安装配置](#安装配置)
3. [快速开始](#快速开始)
4. [核心功能](#核心功能)
5. [高级用法](#高级用法)
6. [配置说明](#配置说明)
7. [故障排除](#故障排除)
8. [API参考](#api参考)

## 系统概述

多模态智能体RAG系统是基于Qwen-Agent框架构建的检索增强生成系统，专门处理PDF文档的多模态内容（文本、图片、表格）。

### 主要特性

- **多模态文档解析**: 支持PDF文档的文本、图片、表格提取
- **智能文档分块**: 保持语义完整性的混合内容分块
- **混合检索**: 结合BM25、向量搜索和多模态检索
- **智能重排序**: 基于多维度评分的结果重排序
- **查询优化**: 查询扩展、重写和自我批判
- **多模态生成**: 集成多模态LLM进行内容理解和生成

### 系统架构

```
文档输入 → 解析器 → 分块器 → 向量存储 → 检索器 → 生成器 → 答案输出
    ↓        ↓        ↓        ↓        ↓        ↓
  PDF文档   多模态   智能     混合     查询     多模态
           内容     分块     检索     优化     LLM
```

## 安装配置

### 环境要求

- Python 3.8+
- 内存: 建议8GB以上
- 存储: 根据文档数量而定
- GPU: 可选，用于加速向量计算

### 安装步骤

1. **克隆项目**
```bash
git clone <repository_url>
cd muti_agent_rag
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置API密钥**
```bash
export DASHSCOPE_API_KEY="your_api_key_here"
```

4. **验证安装**
```bash
python run_tests.py --unit
```

## 快速开始

### 基本使用

```python
from multimodal_rag import MultimodalRAGAgent

# 1. 创建智能体
agent = MultimodalRAGAgent(
    llm_config={
        "model": "qwen-plus",
        "api_key": "your_api_key"
    }
)

# 2. 添加文档
results = agent.add_documents(["document.pdf"])
print(f"添加了 {results['total_chunks']} 个文档块")

# 3. 查询
answer = agent.query("请总结文档的主要内容")
print(answer)
```

### 批量处理

```python
import os

# 批量添加文档
pdf_files = [f for f in os.listdir("./documents") if f.endswith('.pdf')]
for pdf_file in pdf_files:
    result = agent.add_documents([f"./documents/{pdf_file}"])
    print(f"处理 {pdf_file}: {result['total_chunks']} 个块")
```

## 核心功能

### 1. 文档解析

系统支持PDF文档的全面解析：

- **文本提取**: 保持格式和结构
- **图片提取**: 自动提取并进行OCR识别
- **表格识别**: 转换为结构化格式
- **元数据提取**: 页码、字体、位置等信息

### 2. 智能分块

根据内容类型和语义边界进行分块：

```python
from multimodal_rag.processors import SmartChunker

chunker = SmartChunker(
    chunk_size=500,      # 目标块大小
    chunk_overlap=50,    # 重叠大小
    min_chunk_size=50,   # 最小块大小
    max_chunk_size=1000  # 最大块大小
)
```

### 3. 混合检索

结合多种检索方法：

- **BM25检索**: 基于关键词的精确匹配
- **向量检索**: 基于语义相似度
- **多模态检索**: 文本和图像的联合检索

### 4. 查询优化

自动优化用户查询：

```python
# 查询扩展示例
原查询: "图表数据"
扩展后: "图表数据 统计信息 数值 表格"

# 查询重写示例
原查询: "这个文档说了什么？"
重写后: "请总结文档的主要内容和核心观点"
```

## 高级用法

### 自定义配置

```python
from multimodal_rag.config import get_config

# 获取默认配置
config = get_config()

# 修改配置
config['chunk_size'] = 300
config['pdf_parser']['extract_images'] = True
config['ocr']['engine'] = 'easyocr'

# 使用自定义配置
agent = MultimodalRAGAgent(config=config)
```

### 多查询策略

```python
# 不同类型的查询
queries = {
    "总结类": "请总结文档的主要内容",
    "分析类": "文档中有哪些重要数据？",
    "查找类": "文档中提到了哪些案例？",
    "比较类": "不同章节的观点有什么区别？"
}

for query_type, query in queries.items():
    print(f"{query_type}: {agent.query(query)}")
```

### 结果导出

```python
import json

# 获取系统信息
info = agent.get_storage_info()

# 导出结果
export_data = {
    "storage_info": info,
    "queries": [
        {
            "query": "测试查询",
            "answer": agent.query("测试查询")
        }
    ]
}

with open("results.json", "w", encoding="utf-8") as f:
    json.dump(export_data, f, indent=2, ensure_ascii=False)
```

## 配置说明

### 主要配置项

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `chunk_size` | 500 | 文档块大小（token数） |
| `chunk_overlap` | 50 | 块重叠大小 |
| `max_ref_token` | 20000 | 最大参考token数 |
| `top_k` | 10 | 检索结果数量 |
| `score_threshold` | 0.7 | 相关性阈值 |

### PDF解析配置

```python
PDF_PARSER_CONFIG = {
    "extract_images": True,        # 是否提取图片
    "extract_tables": True,        # 是否提取表格
    "ocr_enabled": True,          # 是否启用OCR
    "image_min_size": (50, 50),   # 最小图片尺寸
    "image_max_size": (2048, 2048) # 最大图片尺寸
}
```

### OCR配置

```python
OCR_CONFIG = {
    "engine": "easyocr",              # OCR引擎
    "languages": ["ch_sim", "en"],    # 支持语言
    "confidence_threshold": 0.5       # 置信度阈值
}
```

## 故障排除

### 常见问题

1. **内存不足**
   - 减小`chunk_size`和`max_ref_token`
   - 分批处理大文档

2. **OCR识别错误**
   - 检查图片质量
   - 调整`confidence_threshold`
   - 尝试不同的OCR引擎

3. **检索结果不准确**
   - 调整`score_threshold`
   - 启用查询优化
   - 检查文档分块质量

4. **API调用失败**
   - 检查API密钥配置
   - 确认网络连接
   - 查看API使用限制

### 调试模式

```python
import logging

# 启用调试日志
logging.basicConfig(level=logging.DEBUG)

# 查看详细信息
agent = MultimodalRAGAgent(llm_config=config)
```

### 性能优化

1. **使用GPU加速**
```bash
pip install faiss-gpu
```

2. **调整索引参数**
```python
VECTOR_STORE_CONFIG = {
    "index_type": "HNSW",    # 使用HNSW索引
    "ef_search": 100,        # 搜索参数
    "m": 16                  # 连接数
}
```

3. **缓存配置**
```python
CACHE_CONFIG = {
    "enable_cache": True,
    "cache_dir": "./cache",
    "max_cache_size": "1GB"
}
```

## API参考

### MultimodalRAGAgent

主要智能体类，提供完整的RAG功能。

#### 初始化

```python
MultimodalRAGAgent(
    llm=None,                    # LLM实例
    llm_config=None,            # LLM配置
    system_message=None,        # 系统消息
    storage_path=None,          # 存储路径
    **kwargs
)
```

#### 主要方法

- `add_documents(file_paths)`: 添加文档
- `query(question, **kwargs)`: 查询问答
- `get_storage_info()`: 获取存储信息
- `clear_storage()`: 清空存储

### 配置函数

- `get_config()`: 获取默认配置
- `update_config_from_env()`: 从环境变量更新配置

### 工具类

- `EnhancedPDFParser`: 增强PDF解析器
- `SmartChunker`: 智能分块器
- `MultimodalVectorStore`: 多模态向量存储
- `HybridRetriever`: 混合检索器
- `AnswerGenerator`: 答案生成器

---

更多详细信息请参考源代码和示例文件。

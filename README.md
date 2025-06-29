# 多模态智能体RAG系统

基于Qwen-Agent框架构建的多模态检索增强生成(RAG)系统，专门处理包含Markdown文件和图片的文件夹，支持文本、图片等多模态内容的解析、检索和问答。

## ✨ 核心特性

- 📁 **文件夹输入**: 支持包含MD文件和images文件夹的目录结构
- 📝 **Markdown解析**: 智能解析Markdown文档，提取文本和图片引用
- 🖼️ **图片处理**: 自动处理images文件夹中被引用的图片
- 🔍 **智能检索**: 支持文本和图像的混合检索
- 💬 **多模态问答**: 基于文档内容进行智能问答
- 🌐 **Web界面**: 友好的Gradio界面，支持文件夹路径输入

## 📋 文件夹结构要求

系统需要以下文件夹结构：

```
your_folder/
├── document.md          # 主要的Markdown文档
└── images/             # 图片文件夹（可选）
    ├── image1.png
    ├── image2.jpg
    └── ...
```

### 支持的格式

- **Markdown文件**: `.md`, `.markdown`
- **图片格式**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`
- **图片引用**: 系统会自动匹配MD文件中的图片引用与images文件夹中的实际图片

## 🚀 主要功能

- 📁 **文件夹解析**: 智能识别和解析文件夹结构
- 📝 **Markdown处理**: 完整的Markdown语法支持，包括图片引用
- 🖼️ **图片分析**: 使用多模态模型分析图片内容
- 🔍 **混合检索**: 结合文本搜索和图像搜索
- 💬 **智能问答**: 基于文档内容的多模态问答
- 🌐 **Web界面**: 简洁易用的Gradio界面

## 系统架构

```
多模态智能体RAG系统
├── 文档解析层 (Document Parser)
│   ├── 文件夹解析器 (Folder Parser)
│   ├── Markdown解析器 (Markdown Parser)
│   └── 图片提取器 (Image Extractor)
├── 文档处理层 (Document Processor)
│   ├── 智能分块器 (Smart Chunker)
│   └── 多模态预处理 (Multimodal Preprocessor)
├── 存储层 (Storage Layer)
│   ├── 向量数据库 (Vector Database)
│   └── 元数据存储 (Metadata Store)
├── 检索层 (Retrieval Layer)
│   ├── 混合检索器 (Hybrid Retriever)
│   ├── 重排序器 (Reranker)
│   └── 查询优化器 (Query Optimizer)
└── 生成层 (Generation Layer)
    ├── 多模态LLM (Multimodal LLM)
    └── 回答生成器 (Answer Generator)
```

## 快速开始

### 环境要求

- Python 3.8+
- CUDA (可选，用于GPU加速)

### 安装依赖

```bash
pip install -r requirements.txt
```



### 配置API密钥

创建 `dashscope_key.txt` 文件，添加您的Dashscope API密钥：

```
your-dashscope-api-key-here
```

### Web界面使用（推荐）

启动Web界面：

```bash
# 方式1：直接启动
python webui.py

# 方式2：使用启动脚本（Windows）
start_webui.bat
```

启动后在浏览器中访问：`http://localhost:7860`

**Web界面功能**：
- 📁 **文件夹管理**：输入包含MD文件和images文件夹的目录路径
- 💬 **智能问答**：支持基于文档内容的多模态问答
- 📊 **系统状态**：实时查看文档处理状态和存储信息
- 🔍 **智能检索**：自动分析查询并进行混合检索

详细使用说明请参考：[Web界面使用指南](webui_guide.md)

### 编程接口使用

```python
from multimodal_rag.agent import MultimodalRAGAgent

# 初始化智能体
agent = MultimodalRAGAgent(
    llm_config={
        'model': 'qwen-plus',
        'api_key': 'your-api-key'
    }
)

# 添加文件夹
agent.add_documents(['./data/detective'])  # 包含MD文件和images文件夹的目录

# 智能查询 - 支持多模态问答
result = agent.query_detailed("分析这个文档的主要观点，并结合图片内容进行说明")
print(result['answer'])

# 简单查询
answer = agent.query("这个文档的主要内容是什么？")
print(answer)

# 图片相关查询
image_answer = agent.query("文档中的图片展示了什么内容？")
print(image_answer)
```

## 项目结构

```
muti_agent_rag/
├── multimodal_rag/              # 核心模块
│   ├── __init__.py
│   ├── agent.py                 # 主智能体
│   ├── parsers/                 # 文档解析器
│   │   ├── __init__.py
│   │   ├── folder_parser.py     # 文件夹解析器
│   │   ├── markdown_parser.py   # Markdown解析器
│   │   ├── image_extractor.py   # 图片提取器
│   │   └── ocr_engine.py        # OCR引擎
│   ├── processors/              # 文档处理器
│   │   ├── __init__.py
│   │   └── smart_chunker.py
│   ├── storage/                 # 存储模块
│   │   ├── __init__.py
│   │   ├── vector_store.py
│   │   └── metadata_store.py
│   ├── retrieval/               # 检索模块
│   │   ├── __init__.py
│   │   ├── hybrid_retriever.py
│   │   ├── reranker.py
│   │   └── query_optimizer.py
│   └── generation/              # 生成模块
│       ├── __init__.py
│       ├── multimodal_llm.py
│       └── answer_generator.py
├── examples/                    # 示例代码
├── tests/                       # 测试用例
├── docs/                        # 文档
├── requirements.txt             # 依赖列表
└── README.md                    # 项目说明
```



## 使用示例

### 文件夹结构示例

```
data/detective/
├── detective.md        # 主要文档
└── images/            # 图片文件夹
    ├── cover.jpg
    ├── character.png
    └── scene.gif
```

### 快速测试

```bash
# 测试文件夹解析
python demo_folder_input.py

# 启动Web界面
python webui.py
```

## 技术栈

- **基础框架**: Qwen-Agent
- **文档解析**: Markdown, 图片提取, OCR
- **向量存储**: FAISS, ChromaDB
- **多模态模型**: Qwen-VL, CLIP
- **检索算法**: BM25, Dense Retrieval
- **重排序**: Cross-encoder models
- **Web界面**: Gradio

## 开发计划

- [x] 项目架构设计
- [x] 文件夹解析器实现
- [x] Markdown文档解析
- [x] 图片提取和处理
- [x] 多模态向量存储
- [x] 混合检索和重排序
- [x] 查询重写和优化
- [x] LLM问答生成
- [x] Web界面实现
- [ ] 性能优化和测试完善

## 贡献指南

欢迎提交Issue和Pull Request来改进项目。

## 许可证

MIT License

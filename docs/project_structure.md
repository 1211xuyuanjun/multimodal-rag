# 📁 项目文件结构

## 目录说明

```
muti_agent_rag/
├── README.md                 # 项目说明
├── requirements.txt          # 依赖包列表
├── webui.py                 # Web界面主程序
├── start_webui.bat          # Windows启动脚本
├── dashscope_key.txt        # API密钥文件
├── 
├── multimodal_rag/          # 核心代码包
│   ├── __init__.py
│   ├── agent.py             # 主要智能体
│   ├── config.py            # 配置文件
│   ├── parsers/             # 文档解析器
│   ├── processors/          # 文档处理器
│   ├── retrieval/           # 检索模块
│   ├── generation/          # 生成模块
│   └── storage/             # 存储模块
├── 
├── examples/                # 使用示例
│   ├── basic_usage.py       # 基础使用示例
│   └── advanced_usage.py    # 高级使用示例
├── 
├── docs/                    # 文档目录
│   ├── user_guide.md        # 用户指南
│   ├── webui_guide.md       # Web界面指南
│   ├── webui_features.md    # 功能说明
│   └── *.md                 # 其他文档
├── 
├── scripts/                 # 工具脚本
│   ├── clean_and_manage_storage.py    # 存储管理工具
│   ├── rebuild_vector_index.py        # 索引重建工具
│   ├── regenerate_image_captions.py   # 图像描述生成工具
│   └── organize_project.py            # 项目整理工具
├── 
├── storage/                 # 存储目录
│   ├── webui_storage/       # Web界面存储
│   └── rag_storage/         # RAG系统存储
├── 
├── temp/                    # 临时文件
│   └── temp_uploads/        # 临时上传文件
├── 
├── logs/                    # 日志文件
├── 
└── Qwen-Agent/             # Qwen-Agent依赖包
```

## 文件说明

### 核心文件
- `webui.py`: Web界面主程序，启动Gradio界面
- `multimodal_rag/`: 核心功能模块，包含所有RAG相关功能
- `requirements.txt`: Python依赖包列表

### 配置文件
- `dashscope_key.txt`: Dashscope API密钥
- `multimodal_rag/config.py`: 系统配置参数

### 工具脚本
- `scripts/clean_and_manage_storage.py`: 存储清理和管理
- `scripts/rebuild_vector_index.py`: 重建向量索引
- `scripts/regenerate_image_captions.py`: 重新生成图像描述

### 文档
- `docs/`: 包含所有项目文档和说明
- `README.md`: 项目主要说明文档

### 存储
- `storage/`: 所有持久化存储文件
- `temp/`: 临时文件和缓存

## 使用说明

1. **启动Web界面**: 运行 `python webui.py` 或双击 `start_webui.bat`
2. **查看文档**: 参考 `docs/` 目录下的相关文档
3. **运行示例**: 查看 `examples/` 目录下的示例代码
4. **管理存储**: 使用 `scripts/` 目录下的工具脚本

---
*文档生成时间: 2025-06-28*

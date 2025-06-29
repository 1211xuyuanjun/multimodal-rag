# 更新日志

## v2.0.0 - 文件夹输入专版 (2025-06-29)

### 🎯 重大变更

**移除PDF解析功能，专注于文件夹输入**

基于用户反馈和实际需求，我们决定简化系统架构，移除复杂的PDF解析功能（包括MinerU集成），专注于更实用的文件夹输入方式。

### ✨ 新功能

#### 📁 文件夹输入系统
- **简化输入方式**: 只需提供包含MD文件和images文件夹的目录路径
- **智能文件识别**: 自动识别文件夹中的Markdown文件和图片文件夹
- **精确图片匹配**: 只处理在MD文件中被引用的图片，避免无关图片干扰
- **多格式支持**: 支持 `.md`, `.markdown` 文件和多种图片格式

#### 🌐 优化的Web界面
- **文件夹路径输入**: 替代文件上传，使用文本框输入文件夹路径
- **清晰的使用说明**: 界面中包含详细的文件夹结构要求和示例
- **实时状态反馈**: 显示文档处理状态和存储信息
- **美化的界面设计**: 更新CSS样式，提供更好的用户体验

### 🔧 技术改进

#### 架构简化
- **移除PDF解析器**: 删除 `EnhancedPDFParser` 和 `MinerUParser`
- **移除相关依赖**: 清理 `pdfminer.six`, `pdfplumber` 等PDF处理库
- **简化配置**: 移除PDF和MinerU相关配置项
- **优化导入**: 更新模块导入，只保留必要的解析器

#### 文件夹解析增强
- **保留核心功能**: `FolderParser` 和 `MarkdownParser` 保持完整功能
- **图片处理优化**: 只处理被引用的图片，提高处理效率
- **错误处理改进**: 更好的错误提示和异常处理

### 📋 文件夹结构要求

```
your_folder/
├── document.md          # 主要的Markdown文档
└── images/             # 图片文件夹（可选）
    ├── image1.png
    ├── image2.jpg
    └── ...
```

### 🚀 使用方式

#### Web界面
1. 启动Web界面: `python webui.py`
2. 在文件夹路径输入框中输入目录路径
3. 点击"处理文件夹"按钮
4. 开始智能问答

#### 编程接口
```python
from multimodal_rag.agent import MultimodalRAGAgent

# 初始化智能体
agent = MultimodalRAGAgent(
    llm_config={'model': 'qwen-plus', 'api_key': 'your_api_key'}
)

# 添加文件夹
agent.add_documents(['./data/detective'])

# 进行问答
answer = agent.query("这个文档的主要内容是什么？")
```

### 📊 性能表现

- **处理速度**: 无需复杂的PDF解析，处理速度显著提升
- **内存占用**: 移除大型PDF处理库，内存占用减少
- **稳定性**: 简化架构提高了系统稳定性
- **易用性**: 文件夹输入方式更加直观易用

### 🗂️ 文件变更

#### 新增文件
- `demo_folder_rag.py` - 文件夹输入演示脚本
- `CHANGELOG.md` - 更新日志

#### 修改文件
- `webui.py` - 更新Web界面，支持文件夹路径输入
- `multimodal_rag/agent.py` - 移除PDF解析器初始化
- `multimodal_rag/config.py` - 移除PDF和MinerU配置
- `multimodal_rag/parsers/__init__.py` - 更新导入列表
- `multimodal_rag/parsers/image_extractor.py` - 修复配置引用
- `requirements.txt` - 移除PDF解析依赖
- `README.md` - 更新文档说明

#### 删除文件
- `multimodal_rag/parsers/enhanced_pdf_parser.py`
- `multimodal_rag/parsers/mineru_parser.py`
- `multimodal_rag/parsers/parser_factory.py`
- `demo_mineru_parser.py`
- `test_mineru_simple.py`
- `scripts/install_mineru.py`
- `scripts/configure_mineru.py`

### 🎯 示例演示

系统成功演示了以下功能：

1. **文件夹解析**: 成功解析 `./data/detective` 文件夹
   - 识别MD文件: `detective_250628_221220.md`
   - 处理3张被引用的图片
   - 生成详细的图片描述

2. **多模态问答**: 
   - 文档内容分析
   - 重要概念提取
   - 图片内容识别
   - 复杂查询分解

3. **Web界面**: 
   - 文件夹路径输入
   - 实时处理状态
   - 智能问答交互

### 🔮 未来计划

- **性能优化**: 进一步优化文档处理和检索性能
- **功能扩展**: 支持更多Markdown语法和文档格式
- **用户体验**: 改进Web界面的交互体验
- **API接口**: 提供RESTful API接口

### 💡 使用建议

1. **文件夹准备**: 确保文件夹包含一个主要的MD文件
2. **图片组织**: 将图片放在images文件夹中，并在MD文件中正确引用
3. **路径格式**: 使用相对路径或绝对路径都可以
4. **文件命名**: 建议使用英文文件名避免编码问题

---

**注意**: 此版本不再支持PDF文件直接上传。如需处理PDF文档，请先使用其他工具将其转换为Markdown格式，然后使用文件夹输入方式。

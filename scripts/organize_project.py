#!/usr/bin/env python3
"""
项目文件整理脚本

该脚本用于：
1. 创建合理的项目目录结构
2. 移动文件到合适的位置
3. 删除无关和临时文件
4. 清理项目根目录
"""

import os
import shutil
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProjectOrganizer:
    """项目文件整理器"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        
        # 定义目标目录结构
        self.target_structure = {
            "docs": "文档目录",
            "scripts": "脚本工具目录", 
            "storage": "存储目录",
            "temp": "临时文件目录",
            "logs": "日志目录"
        }
        
        # 定义文件移动规则
        self.move_rules = {
            # 文档文件 -> docs/
            "docs": [
                "*.md",
                "webui_guide.md",
                "webui_features.md", 
                "ui_improvements_summary.md",
                "answer_quality_improvements.md",
                "comprehensive_demo_results.md",
                "图像查询改进成果总结.md",
                "图像查询问题分析与解决方案.md", 
                "缓存和数据库管理问题分析.md",
                "页面布局优化说明.md"
            ],
            
            # 脚本工具 -> scripts/
            "scripts": [
                "clean_and_manage_storage.py",
                "rebuild_vector_index.py", 
                "regenerate_image_captions.py",
                "organize_project.py"
            ],
            
            # 存储相关 -> storage/
            "storage": [
                "webui_storage",
                "rag_storage"
            ],
            
            # 临时文件 -> temp/
            "temp": [
                "temp_uploads",
                "__pycache__"
            ]
        }
        
        # 定义要删除的文件/目录
        self.files_to_delete = [
            "detective.pdf",  # 测试文件
            "__pycache__",    # Python缓存
            "*.pyc",          # Python编译文件
            "webui_storage/metadata.db",  # 旧的数据库文件
        ]
        
        # 定义要保留在根目录的文件
        self.keep_in_root = [
            "README.md",
            "requirements.txt", 
            "webui.py",
            "start_webui.bat",
            "dashscope_key.txt",
            "multimodal_rag",  # 主要代码包
            "examples",        # 示例代码
            "Qwen-Agent"       # 依赖包
        ]
    
    def create_directories(self):
        """创建目标目录结构"""
        logger.info("创建目录结构...")
        
        for dir_name, description in self.target_structure.items():
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"创建目录: {dir_name} ({description})")
            else:
                logger.info(f"目录已存在: {dir_name}")
    
    def move_files(self):
        """根据规则移动文件"""
        logger.info("移动文件到合适位置...")
        
        for target_dir, patterns in self.move_rules.items():
            target_path = self.project_root / target_dir
            
            for pattern in patterns:
                if "*" in pattern:
                    # 处理通配符模式
                    for file_path in self.project_root.glob(pattern):
                        if file_path.is_file() and file_path.name not in self.keep_in_root:
                            self._move_file(file_path, target_path / file_path.name)
                else:
                    # 处理具体文件/目录
                    source_path = self.project_root / pattern
                    if source_path.exists() and pattern not in self.keep_in_root:
                        target_file_path = target_path / pattern
                        self._move_file(source_path, target_file_path)
    
    def _move_file(self, source: Path, target: Path):
        """移动单个文件或目录"""
        try:
            if source.exists():
                # 确保目标目录存在
                target.parent.mkdir(parents=True, exist_ok=True)
                
                # 如果目标已存在，先删除
                if target.exists():
                    if target.is_dir():
                        shutil.rmtree(target)
                    else:
                        target.unlink()
                
                # 移动文件/目录
                shutil.move(str(source), str(target))
                logger.info(f"移动: {source.name} -> {target.parent.name}/")
                
        except Exception as e:
            logger.error(f"移动文件失败 {source} -> {target}: {str(e)}")
    
    def delete_unwanted_files(self):
        """删除不需要的文件"""
        logger.info("删除无关文件...")
        
        for pattern in self.files_to_delete:
            if "*" in pattern:
                # 处理通配符
                for file_path in self.project_root.rglob(pattern):
                    self._delete_file(file_path)
            else:
                # 处理具体文件
                file_path = self.project_root / pattern
                if file_path.exists():
                    self._delete_file(file_path)
    
    def _delete_file(self, file_path: Path):
        """删除单个文件或目录"""
        try:
            if file_path.is_dir():
                shutil.rmtree(file_path)
                logger.info(f"删除目录: {file_path}")
            else:
                file_path.unlink()
                logger.info(f"删除文件: {file_path}")
        except Exception as e:
            logger.error(f"删除失败 {file_path}: {str(e)}")
    
    def create_gitignore(self):
        """创建.gitignore文件"""
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Project specific
temp/
logs/
storage/
*.log
dashscope_key.txt

# OS
.DS_Store
Thumbs.db
"""
        
        gitignore_path = self.project_root / ".gitignore"
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
        logger.info("创建 .gitignore 文件")
    
    def create_project_structure_doc(self):
        """创建项目结构说明文档"""
        structure_doc = """# 📁 项目文件结构

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
"""
        
        doc_path = self.project_root / "docs" / "project_structure.md"
        with open(doc_path, 'w', encoding='utf-8') as f:
            f.write(structure_doc)
        logger.info("创建项目结构说明文档")
    
    def organize(self):
        """执行完整的项目整理"""
        logger.info("🧹 开始整理项目文件结构...")
        
        # 1. 创建目录结构
        self.create_directories()
        
        # 2. 移动文件到合适位置
        self.move_files()
        
        # 3. 删除无关文件
        self.delete_unwanted_files()
        
        # 4. 创建配置文件
        self.create_gitignore()
        
        # 5. 创建文档
        self.create_project_structure_doc()
        
        logger.info("✅ 项目文件整理完成！")
        
        # 显示最终结构
        self.show_final_structure()
    
    def show_final_structure(self):
        """显示最终的项目结构"""
        logger.info("\n📁 最终项目结构:")
        for root, dirs, files in os.walk(self.project_root):
            level = root.replace(str(self.project_root), '').count(os.sep)
            indent = ' ' * 2 * level
            logger.info(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files[:5]:  # 只显示前5个文件
                logger.info(f"{subindent}{file}")
            if len(files) > 5:
                logger.info(f"{subindent}... 和其他 {len(files)-5} 个文件")

def main():
    """主函数"""
    print("🧹 项目文件整理工具")
    print("=" * 50)
    
    organizer = ProjectOrganizer()
    
    # 确认操作
    response = input("确认要整理项目文件结构吗？这将移动和删除一些文件。(yes/no): ").strip().lower()
    if response != "yes":
        print("操作已取消")
        return
    
    organizer.organize()
    print("\n🎉 项目整理完成！")
    print("请查看 docs/project_structure.md 了解新的文件结构")

if __name__ == "__main__":
    main()

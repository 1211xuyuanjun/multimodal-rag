"""
多模态RAG系统Web界面

基于Gradio构建的用户友好界面，支持文档上传、查询处理和结果展示。
"""

import os
import sys
import gradio as gr
from pathlib import Path
import logging
from typing import List, Tuple
import shutil
import tkinter as tk
from tkinter import filedialog

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from multimodal_rag.agent import MultimodalRAGAgent

def select_folder():
    """打开文件夹选择对话框"""
    try:
        # 创建一个隐藏的tkinter根窗口
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        root.attributes('-topmost', True)  # 置顶显示

        # 打开文件夹选择对话框
        folder_path = filedialog.askdirectory(
            title="选择包含MD文件的文件夹",
            initialdir="."
        )

        root.destroy()  # 销毁窗口

        return folder_path if folder_path else ""
    except Exception as e:
        logger.error(f"文件夹选择失败: {str(e)}")
        return ""

class RAGWebUI:
    """RAG系统Web界面类"""
    
    def __init__(self):
        self.agent = None
        self.api_key = None
        self.storage_path = "./storage/webui_storage"
        self.temp_dir = "./temp/temp_uploads"
        
        # 创建必要的目录
        os.makedirs(self.storage_path, exist_ok=True)
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # 加载API密钥
        self._load_api_key()
        
        # 初始化智能体
        if self.api_key:
            self._initialize_agent()
    
    def _load_api_key(self):
        """加载API密钥"""
        key_file = Path("dashscope_key.txt")
        if key_file.exists():
            with open(key_file, 'r', encoding='utf-8') as f:
                self.api_key = f.read().strip()
                logger.info("API密钥加载成功")
        else:
            logger.warning("API密钥文件不存在")
    
    def _initialize_agent(self):
        """初始化RAG智能体"""
        try:
            self.agent = MultimodalRAGAgent(
                llm_config={
                    'model': 'qwen-plus',
                    'api_key': self.api_key
                },
                storage_path=self.storage_path
            )
            logger.info("RAG智能体初始化成功")
        except Exception as e:
            logger.error(f"RAG智能体初始化失败: {str(e)}")
            self.agent = None
    
    def upload_folder(self, folder_path: str) -> Tuple[str, str]:
        """
        上传并处理文件夹

        Args:
            folder_path: 文件夹路径

        Returns:
            处理结果信息和存储状态
        """
        if not self.agent:
            return "❌ 系统未初始化，请检查API密钥配置", ""

        if not folder_path:
            return "⚠️ 请选择文件夹", ""

        # 处理FileExplorer返回的路径
        if isinstance(folder_path, str):
            folder_path = folder_path.strip()
        else:
            return "⚠️ 请选择一个有效的文件夹", ""

        # FileExplorer返回的是相对路径，需要转换为绝对路径
        if not os.path.isabs(folder_path):
            folder_path = os.path.abspath(folder_path)

        if not os.path.exists(folder_path):
            return f"❌ 文件夹不存在: {folder_path}", ""

        if not os.path.isdir(folder_path):
            return f"❌ 路径不是文件夹: {folder_path}", ""

        try:
            # 处理文件夹
            result = self.agent.add_documents([folder_path])

            if not result:
                return "❌ 文件夹处理失败", ""
            
            # 格式化结果
            success_count = len(result.get('successful', []))
            failed_count = len(result.get('failed', []))
            total_chunks = result.get('total_chunks', 0)
            
            status_msg = f"✅ 文档处理完成\n"
            status_msg += f"📄 成功处理: {success_count} 个文件\n"
            status_msg += f"❌ 处理失败: {failed_count} 个文件\n"
            status_msg += f"📦 生成块数: {total_chunks} 个\n"
            
            if result.get('failed'):
                status_msg += "\n失败文件:\n"
                for failed in result['failed']:
                    status_msg += f"  - {failed.get('file', 'Unknown')}: {failed.get('error', 'Unknown error')}\n"
            
            # 获取存储信息
            storage_info = self.agent.get_storage_info()
            storage_msg = f"📊 存储状态:\n"
            storage_msg += f"  - 文档总数: {storage_info.get('total_documents', 0)}\n"
            storage_msg += f"  - 文本块数: {storage_info.get('text_count', 0)}\n"
            storage_msg += f"  - 图像块数: {storage_info.get('image_count', 0)}\n"
            storage_msg += f"  - 总块数: {storage_info.get('total_count', 0)}"
            
            return status_msg, storage_msg
            
        except Exception as e:
            logger.error(f"文档处理失败: {str(e)}")
            return f"❌ 文档处理失败: {str(e)}", ""
    

    
    def process_query(self, query: str, use_intelligent: bool = True, search_type: str = "both") -> Tuple[str, str]:
        """
        处理查询并生成答案
        
        Args:
            query: 用户查询
            use_intelligent: 是否使用智能处理
            search_type: 搜索类型 (text/image/both)
            
        Returns:
            答案和处理信息
        """
        if not self.agent:
            return "❌ 系统未初始化，请检查API密钥配置", ""
        
        if not query.strip():
            return "⚠️ 请输入查询内容", ""
        
        try:
            # 获取存储信息检查是否有文档
            storage_info = self.agent.get_storage_info()
            if storage_info.get('total_count', 0) == 0:
                return "⚠️ 请先上传文档再进行查询", ""
            
            # 处理查询
            if use_intelligent:
                result = self.agent.query_detailed(
                    query, 
                    use_intelligent_processing=True,
                    search_type=search_type
                )
                answer = result.get('answer', '未找到答案')
                
                # 格式化处理信息
                processing_info = result.get('processing_info', {})
                info_msg = f"🔧 处理信息:\n"
                info_msg += f"  - 查询类型: {result.get('query_type', 'unknown')}\n"
                info_msg += f"  - 使用分解: {'是' if processing_info.get('decomposition_used', False) else '否'}\n"
                info_msg += f"  - 使用汇总: {'是' if processing_info.get('synthesis_used', False) else '否'}\n"
                info_msg += f"  - 子查询数: {processing_info.get('total_sub_queries', 0)}\n"
                info_msg += f"  - 检索结果数: {processing_info.get('total_results', 0)}\n"
                
                # 显示子查询信息
                sub_queries = result.get('sub_queries', [])
                if len(sub_queries) > 1:
                    info_msg += f"\n📋 子查询执行:\n"
                    for i, sq in enumerate(sub_queries, 1):
                        info_msg += f"  {i}. {sq['query']}\n"
                        info_msg += f"     结果数: {sq['results_count']}\n"
                
            else:
                answer = self.agent.query(
                    query, 
                    use_intelligent_processing=False,
                    search_type=search_type
                )
                info_msg = "🔧 处理信息:\n  - 使用简单查询模式"
            
            return answer, info_msg
            
        except Exception as e:
            logger.error(f"查询处理失败: {str(e)}")
            return f"❌ 查询处理失败: {str(e)}", ""
    
    def get_system_status(self) -> str:
        """获取系统状态"""
        if not self.agent:
            return "❌ 系统未初始化"
        
        try:
            storage_info = self.agent.get_storage_info()
            config = self.agent.get_processing_config()
            
            status = f"🟢 系统状态: 正常运行\n\n"
            status += f"📊 存储信息:\n"
            status += f"  - 存储路径: {storage_info.get('storage_path', 'Unknown')}\n"
            status += f"  - 文档总数: {storage_info.get('total_documents', 0)}\n"
            status += f"  - 文本块数: {storage_info.get('text_count', 0)}\n"
            status += f"  - 图像块数: {storage_info.get('image_count', 0)}\n"
            status += f"  - 总块数: {storage_info.get('total_count', 0)}\n\n"
            
            processor_config = config.get('intelligent_processor', {}).get('processor_config', {})
            status += f"⚙️ 配置信息:\n"
            status += f"  - 启用分解: {'是' if processor_config.get('enable_decomposition', False) else '否'}\n"
            status += f"  - 分解阈值: {processor_config.get('decomposition_threshold', 0)}\n"
            status += f"  - 最大子查询数: {processor_config.get('max_sub_queries', 0)}\n"
            status += f"  - 启用汇总: {'是' if processor_config.get('enable_synthesis', False) else '否'}\n"
            
            return status
            
        except Exception as e:
            return f"❌ 获取系统状态失败: {str(e)}"
    
    def clear_storage(self) -> str:
        """清空存储"""
        if not self.agent:
            return "❌ 系统未初始化"
        
        try:
            self.agent.clear_storage()
            return "✅ 存储已清空"
        except Exception as e:
            return f"❌ 清空存储失败: {str(e)}"

def create_interface():
    """创建Gradio界面"""

    # 初始化Web UI
    webui = RAGWebUI()

    # 创建界面
    with gr.Blocks(
        title="🤖 智能多模态RAG系统",
        theme=gr.themes.Soft(),
        css="""
        /* 全局样式 - 优化布局 */
        .gradio-container {
            max-width: 1800px !important;
            margin: 0 auto;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 10px;
        }

        /* 主容器样式 - 优化间距 */
        .main-container {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            margin: 10px;
            padding: 25px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            backdrop-filter: blur(10px);
        }

        /* 标题样式 */
        .main-title {
            background: linear-gradient(45deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }

        .subtitle {
            text-align: center;
            color: #666;
            font-size: 1.2em;
            margin-bottom: 30px;
        }

        /* 文件夹选择器区域 - 优化样式 */
        .folder-input {
            border: 2px solid #667eea;
            border-radius: 8px;
            padding: 12px;
            background: linear-gradient(135deg, #f8f9ff 0%, #e8f0ff 100%);
            transition: all 0.3s ease;
            margin: 10px 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }

        .folder-input:focus {
            border-color: #764ba2;
            background: linear-gradient(135deg, #f0f4ff 0%, #e0ebff 100%);
            box-shadow: 0 0 10px rgba(102, 126, 234, 0.2);
        }

        /* 选择文件夹按钮样式 */
        .select-folder-button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            color: white;
            font-weight: 600;
            transition: all 0.3s ease;
            border-radius: 8px;
            height: 42px;
        }

        .select-folder-button:hover {
            background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }

        .info-text {
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 15px 0;
            border-radius: 0 8px 8px 0;
            font-size: 0.9em;
        }

        .info-text ul {
            margin: 10px 0;
            padding-left: 20px;
        }

        .info-text li {
            margin: 5px 0;
        }

        /* 状态框样式 - 优化视觉效果 */
        .status-box {
            background: linear-gradient(135deg, #e8f5e8 0%, #f0fff0 100%);
            border: 2px solid #4CAF50;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            box-shadow: 0 4px 12px rgba(76, 175, 80, 0.08);
            font-size: 0.9em;
        }

        /* 按钮样式 - 优化尺寸和视觉效果 */
        .primary-button {
            background: linear-gradient(45deg, #667eea, #764ba2) !important;
            border: none !important;
            border-radius: 20px !important;
            padding: 10px 25px !important;
            color: white !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.25) !important;
            font-size: 0.95em !important;
        }

        .primary-button:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 18px rgba(102, 126, 234, 0.35) !important;
        }

        .secondary-button {
            background: linear-gradient(45deg, #f093fb, #f5576c) !important;
            border: none !important;
            border-radius: 18px !important;
            color: white !important;
            transition: all 0.3s ease !important;
            padding: 8px 20px !important;
            font-size: 0.9em !important;
        }

        .secondary-button:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 12px rgba(240, 147, 251, 0.3) !important;
        }

        /* 输入框样式 - 优化视觉效果 */
        .question-input {
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            padding: 12px 15px;
            font-size: 15px;
            transition: all 0.3s ease;
            background: white;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        }

        .question-input:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.08);
            outline: none;
        }

        /* 答案区域样式 - 优化布局 */
        .answer-area {
            background: linear-gradient(135deg, #f8f9ff 0%, #e8f0ff 100%);
            border: 2px solid #e0e8ff;
            border-radius: 12px;
            padding: 18px;
            margin: 10px 0;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.08);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            font-size: 14px;
        }

        /* 处理信息样式 - 优化布局 */
        .process-info {
            background: linear-gradient(135deg, #fff8e1 0%, #ffecb3 100%);
            border: 2px solid #ffc107;
            border-radius: 12px;
            padding: 15px;
            margin: 10px 0;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            line-height: 1.4;
            box-shadow: 0 4px 12px rgba(255, 193, 7, 0.08);
        }

        /* 标签页样式 */
        .tab-nav {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%) !important;
            border-radius: 15px 15px 0 0 !important;
            padding: 10px !important;
        }

        .tab-nav button {
            background: rgba(255, 255, 255, 0.2) !important;
            color: white !important;
            border: none !important;
            border-radius: 10px !important;
            margin: 0 5px !important;
            padding: 10px 20px !important;
            font-weight: bold !important;
            transition: all 0.3s ease !important;
        }

        .tab-nav button.selected {
            background: rgba(255, 255, 255, 0.9) !important;
            color: #667eea !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2) !important;
        }

        /* 卡片样式 - 优化视觉效果 */
        .info-card {
            background: linear-gradient(135deg, #f8f9ff 0%, #e8f0ff 100%);
            border: 2px solid #e0e8ff;
            border-radius: 12px;
            padding: 15px 20px;
            margin: 10px 0;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.08);
            transition: all 0.3s ease;
        }

        .info-card:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.12);
        }

        .info-card h2, .info-card h3, .info-card h4 {
            color: #4a5568;
            margin-bottom: 8px;
            font-weight: 600;
        }

        .info-card p {
            color: #718096;
            margin-bottom: 0;
            font-size: 0.95em;
        }

        /* 示例问题样式 */
        .example-questions {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 15px;
            padding: 25px;
            margin: 20px 0;
            border: 2px solid #dee2e6;
        }

        .example-questions h3 {
            color: #495057;
            margin-bottom: 15px;
        }

        .example-questions ul {
            list-style: none;
            padding: 0;
        }

        .example-questions li {
            background: white;
            margin: 8px 0;
            padding: 12px 15px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            transition: all 0.3s ease;
            cursor: pointer;
        }

        .example-questions li:hover {
            background: #f8f9ff;
            transform: translateX(5px);
            box-shadow: 0 3px 10px rgba(102, 126, 234, 0.1);
        }

        /* 动画效果 */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(30px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .fade-in {
            animation: fadeInUp 0.6s ease-out;
        }

        /* 响应式设计 */
        @media (max-width: 768px) {
            .gradio-container {
                margin: 10px;
            }

            .main-container {
                margin: 10px;
                padding: 20px;
            }

            .main-title {
                font-size: 2em;
            }
        }
        """
    ) as interface:

        with gr.Column(elem_classes=["main-container"]):
            gr.HTML("""
            <div class="main-title fade-in">🤖 智能多模态RAG系统</div>
            <div class="subtitle fade-in">
                🚀 基于大语言模型的智能文档问答系统<br>
                📚 支持PDF解析 • 🧠 智能查询分解 • 🔍 多模态检索 • ✨ 答案生成
            </div>
            """)

        # 优化后的单页面布局 - 移除标签页，直接展示内容
        # 文档上传区域 - 优化布局比例
        with gr.Row():
            with gr.Column(scale=3):
                gr.HTML('<div class="info-card"><h3>📁 文档管理</h3></div>')

                # 文件夹选择器
                with gr.Row():
                    folder_path = gr.Textbox(
                        label="📂 选择的文件夹路径",
                        placeholder="点击右侧按钮选择文件夹...",
                        lines=1,
                        scale=4,
                        elem_classes=["folder-input"],
                        interactive=False
                    )
                    select_folder_btn = gr.Button(
                        "📁 选择文件夹",
                        variant="secondary",
                        scale=1,
                        elem_classes=["select-folder-button"]
                    )

                # 说明文本
                gr.HTML('''
                <div class="info-text">
                    <p><strong>📋 使用说明：</strong></p>
                    <ul>
                        <li>📁 点击"选择文件夹"按钮打开文件夹选择对话框</li>
                        <li>📄 选择包含 .md 或 .markdown 文件的文件夹</li>
                        <li>🖼️ 文件夹可包含 images 子文件夹（可选）</li>
                        <li>✅ 选择后点击"处理文件夹"按钮开始处理</li>
                    </ul>
                </div>
                ''')

                with gr.Row():
                    upload_btn = gr.Button(
                        "📁 处理文件夹",
                        variant="primary",
                        size="lg",
                        elem_classes=["primary-button"]
                    )
                    clear_btn = gr.Button(
                        "🗑️ 清空存储",
                        variant="secondary",
                        size="lg",
                        elem_classes=["secondary-button"]
                    )

            with gr.Column(scale=2):
                gr.HTML('<div class="info-card"><h3>📊 系统状态</h3></div>')
                storage_status = gr.Textbox(
                    label="",
                    lines=6,
                    interactive=False,
                    elem_classes=["status-box"],
                    show_label=False,
                    placeholder="🔄 系统状态加载中..."
                )
                status_btn = gr.Button(
                    "🔄 刷新状态",
                    variant="secondary",
                    size="lg",
                    elem_classes=["secondary-button"]
                )

        # 处理结果显示
        upload_result = gr.Textbox(
            label="📋 处理结果",
            lines=3,
            interactive=False,
            visible=False,
            elem_classes=["info-card"]
        )

        gr.HTML('<div style="margin: 25px 0; border-top: 2px solid #e0e0e0;"></div>')

        # 问答区域 - 优化布局
        gr.HTML('<div class="info-card"><h2>💬 智能问答</h2><p>🧠 所有查询都将使用智能分解和汇总技术</p></div>')

        with gr.Row():
            with gr.Column(scale=3):
                question_input = gr.Textbox(
                    label="🤔 输入您的问题",
                    placeholder="💡 例如：这个文档的主要内容是什么？请总结文档的核心观点和重要数据...",
                    lines=3,
                    elem_classes=["question-input"]
                )

            with gr.Column(scale=2):
                # 移除智能处理选项，默认全部使用智能查询
                intelligent_mode = gr.State(value=True)  # 隐藏的状态，始终为True

                gr.HTML('<div class="info-card"><h4>🔍 搜索配置</h4></div>')
                search_type = gr.Radio(
                    choices=[("🔤📷 文本+图像", "both"), ("🔤 仅文本", "text"), ("📷 仅图像", "image")],
                    value="both",
                    label="搜索类型",
                    info="推荐使用文本+图像获得最佳效果"
                )

                ask_btn = gr.Button(
                    "🚀 开始提问",
                    variant="primary",
                    size="lg",
                    elem_classes=["primary-button"]
                )

        # 答案显示区域 - 优化布局比例
        with gr.Row():
            with gr.Column(scale=7):
                gr.HTML('<div class="info-card"><h3>📝 智能答案</h3></div>')
                answer_output = gr.Textbox(
                    label="",
                    lines=15,
                    interactive=False,
                    placeholder="🎯 请先上传PDF文档，然后输入您的问题...\n\n✨ 系统将自动：\n• 🧠 分析查询复杂度\n• 🔍 智能检索相关内容\n• 📊 分解复杂问题\n• 🎨 生成完整答案",
                    elem_classes=["answer-area"],
                    show_label=False
                )

            with gr.Column(scale=3):
                gr.HTML('<div class="info-card"><h3>🔧 处理详情</h3></div>')
                process_info = gr.Textbox(
                    label="",
                    lines=15,
                    interactive=False,
                    elem_classes=["process-info"],
                    show_label=False,
                    placeholder="📊 处理信息将在这里显示：\n\n🔍 查询分析\n📈 复杂度评分\n🔀 子查询分解\n📋 执行计划\n📊 检索统计\n⏱️ 处理时间"
                )

        # 示例问题 - 优化布局
        gr.HTML("""
        <div class="example-questions">
            <h3>💡 示例问题 - 点击可快速填入</h3>

            <div style="display: flex; gap: 30px; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 300px;">
                    <h4>🔍 简单查询</h4>
                    <ul>
                        <li onclick="document.querySelector('textarea[placeholder*=\"例如\"]').value='这个文档的主要内容是什么？'">📄 这个文档的主要内容是什么？</li>
                        <li onclick="document.querySelector('textarea[placeholder*=\"例如\"]').value='作者的主要观点和结论是什么？'">💭 作者的主要观点和结论是什么？</li>
                        <li onclick="document.querySelector('textarea[placeholder*=\"例如\"]').value='文档中提到了哪些重要数据和统计信息？'">📊 文档中提到了哪些重要数据和统计信息？</li>
                    </ul>
                </div>

                <div style="flex: 1; min-width: 300px;">
                    <h4>🧠 复杂查询（自动分解）</h4>
                    <ul>
                        <li onclick="document.querySelector('textarea[placeholder*=\"例如\"]').value='比较文档中不同方法的优缺点，并分析其适用场景'">⚖️ 比较文档中不同方法的优缺点，并分析其适用场景</li>
                        <li onclick="document.querySelector('textarea[placeholder*=\"例如\"]').value='分析文档的研究方法、实验设计、结果和结论'">🔬 分析文档的研究方法、实验设计、结果和结论</li>
                        <li onclick="document.querySelector('textarea[placeholder*=\"例如\"]').value='总结文档的核心贡献、创新点和实际应用价值'">✨ 总结文档的核心贡献、创新点和实际应用价值</li>
                    </ul>
                </div>

                <div style="flex: 1; min-width: 300px;">
                    <h4>🖼️ 多模态查询</h4>
                    <ul>
                        <li onclick="document.querySelector('textarea[placeholder*=\"例如\"]').value='文档中的图表和图像说明了什么重要信息？'">📈 文档中的图表和图像说明了什么重要信息？</li>
                        <li onclick="document.querySelector('textarea[placeholder*=\"例如\"]').value='描述文档中的视觉元素及其与文本的关联'">🎨 描述文档中的视觉元素及其与文本的关联</li>
                        <li onclick="document.querySelector('textarea[placeholder*=\"例如\"]').value='分析文档的整体布局和信息组织结构'">📐 分析文档的整体布局和信息组织结构</li>
                    </ul>
                </div>
            </div>
        </div>
        """)

        # 绑定事件
        def upload_and_show_result(folder_path):
            result, status = webui.upload_folder(folder_path)
            return result, status, gr.update(visible=True)

        # 文件夹选择按钮事件
        select_folder_btn.click(
            fn=select_folder,
            outputs=[folder_path]
        )

        upload_btn.click(
            fn=upload_and_show_result,
            inputs=[folder_path],
            outputs=[upload_result, storage_status, upload_result]
        )

        clear_btn.click(
            fn=webui.clear_storage,
            outputs=[storage_status]
        )

        status_btn.click(
            fn=webui.get_system_status,
            outputs=[storage_status]
        )

        ask_btn.click(
            fn=webui.process_query,
            inputs=[question_input, intelligent_mode, search_type],
            outputs=[answer_output, process_info]
        )

        # 初始化状态
        interface.load(
            fn=webui.get_system_status,
            outputs=[storage_status]
        )

    return interface

if __name__ == "__main__":
    # 创建并启动界面
    interface = create_interface()
    
    # 启动服务
    interface.launch(
        server_name="0.0.0.0",
        server_port=7861,
        share=False,
        debug=True,
        show_error=True
    )

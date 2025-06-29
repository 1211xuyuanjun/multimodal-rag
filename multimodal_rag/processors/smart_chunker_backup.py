"""
智能文档分块器

实现智能文档分块，支持文本、图片、表格的混合分块，保持语义完整性。
"""

import os
import re
import sys
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging

# 添加Qwen-Agent到路径
sys.path.append(str(Path(__file__).parent.parent.parent / "Qwen-Agent"))

from qwen_agent.utils.tokenization_qwen import count_tokens

from ..data_structures import ParsedDocument, DocumentChunk
from ..config import DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP, DOCUMENT_PROCESSING_CONFIG

logger = logging.getLogger(__name__)


# DocumentChunk现在从data_structures导入


class SmartChunker:
    """
    智能文档分块器

    核心功能：
    1. 智能文本分块（保持语义完整性）
    2. 图片内容处理（支持简化和详细描述）
    3. 表格内容处理
    """

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        multimodal_llm: Optional[Any] = None,
        enable_image_description: bool = True
    ):
        """
        初始化分块器

        Args:
            chunk_size: 目标块大小（token数）
            chunk_overlap: 块重叠大小
            multimodal_llm: 多模态LLM实例，用于图像分析
            enable_image_description: 是否启用详细图像描述生成
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.multimodal_llm = multimodal_llm
        self.enable_image_description = enable_image_description
    
    def chunk_document(self, parsed_doc: ParsedDocument) -> List[DocumentChunk]:
        """
        对解析后的文档进行分块
        
        Args:
            parsed_doc: 解析后的文档
            
        Returns:
            文档块列表
        """
        logger.info(f"开始对文档进行智能分块: {parsed_doc.source}")
        
        chunks = []
        
        # 处理每一页
        for page_idx, page in enumerate(parsed_doc.pages):
            page_chunks = self._chunk_page(page, page_idx, parsed_doc.source)
            chunks.extend(page_chunks)
        
        # 处理独立的图片
        for img_idx, image in enumerate(parsed_doc.images):
            img_chunk = self._create_image_chunk(image, img_idx, parsed_doc.source)
            if img_chunk:
                chunks.append(img_chunk)
        
        logger.info(f"文档分块完成: 共生成{len(chunks)}个块")
        return chunks
    
    def _chunk_page(self, page: Dict[str, Any], page_idx: int, source: str) -> List[DocumentChunk]:
        """
        对单页进行分块
        
        Args:
            page: 页面数据
            page_idx: 页面索引
            source: 文档来源
            
        Returns:
            页面块列表
        """
        chunks = []
        current_text = ""
        current_elements = []
        
        for content_item in page.get('content', []):
            content_type = content_item.get('content_type', 'text')
            
            if content_type == 'text':
                text = content_item.get('text', '').strip()
                if text:
                    current_text += text + "\n"
                    current_elements.append(content_item)
            
            elif content_type == 'table':
                # 先处理累积的文本
                if current_text.strip():
                    text_chunks = self._chunk_text(
                        current_text.strip(),
                        page_idx,
                        source,
                        current_elements
                    )
                    chunks.extend(text_chunks)
                    current_text = ""
                    current_elements = []
                
                # 处理表格
                table_chunk = self._create_table_chunk(content_item, page_idx, source)
                if table_chunk:
                    chunks.append(table_chunk)
            
            elif content_type == 'image':
                # 先处理累积的文本
                if current_text.strip():
                    text_chunks = self._chunk_text(
                        current_text.strip(),
                        page_idx,
                        source,
                        current_elements
                    )
                    chunks.extend(text_chunks)
                    current_text = ""
                    current_elements = []
                
                # 处理图片
                img_chunk = self._create_image_chunk(content_item, page_idx, source)
                if img_chunk:
                    chunks.append(img_chunk)
        
        # 处理剩余的文本
        if current_text.strip():
            text_chunks = self._chunk_text(
                current_text.strip(),
                page_idx,
                source,
                current_elements
            )
            chunks.extend(text_chunks)
        
        return chunks
    
    def _chunk_text(
        self,
        text: str,
        page_idx: int,
        source: str,
        elements: List[Dict[str, Any]]
    ) -> List[DocumentChunk]:
        """
        对文本进行智能分块

        Args:
            text: 文本内容
            page_idx: 页面索引
            source: 文档来源
            elements: 相关元素

        Returns:
            文本块列表
        """
        # 如果文本很短，直接返回一个块
        if count_tokens(text) <= self.chunk_size:
            metadata = {
                'source': source,
                'page_num': page_idx + 1,
                'chunk_index': 0,
                'elements': elements
            }
            return [DocumentChunk(text, 'text', metadata)]

        # 简单分割文本（按段落和句子）
        chunks = []
        paragraphs = text.split('\n\n')

        current_chunk = ""
        chunk_index = 0

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # 检查是否需要开始新块
            test_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph

            if count_tokens(test_chunk) > self.chunk_size and current_chunk:
                # 保存当前块
                metadata = {
                    'source': source,
                    'page_num': page_idx + 1,
                    'chunk_index': chunk_index,
                    'elements': elements
                }
                chunks.append(DocumentChunk(current_chunk.strip(), 'text', metadata))
                chunk_index += 1
                current_chunk = paragraph
            else:
                current_chunk = test_chunk

        # 保存最后一个块
        if current_chunk.strip():
            metadata = {
                'source': source,
                'page_num': page_idx + 1,
                'chunk_index': chunk_index,
                'elements': elements
            }
            chunks.append(DocumentChunk(current_chunk.strip(), 'text', metadata))

        return chunks
    

    
    def _create_table_chunk(self, table_item: Dict[str, Any], page_idx: int, source: str) -> Optional[DocumentChunk]:
        """
        创建表格块
        
        Args:
            table_item: 表格项
            page_idx: 页面索引
            source: 文档来源
            
        Returns:
            表格块
        """
        table_content = table_item.get('table', '').strip()
        if not table_content:
            return None
        
        metadata = {
            'source': source,
            'page_num': page_idx + 1,
            'content_type': 'table',
            'bbox': table_item.get('bbox'),
            'font_size': table_item.get('font-size')
        }
        
        return DocumentChunk(table_content, 'table', metadata)
    
    def _create_image_chunk(self, image_item: Dict[str, Any], item_idx: int, source: str) -> Optional[DocumentChunk]:
        """
        创建图片块

        Args:
            image_item: 图片项
            item_idx: 项目索引
            source: 文档来源

        Returns:
            图片块
        """
        content_parts = []

        # 添加图片基本信息
        if 'image_path' in image_item:
            image_path = image_item['image_path']
            content_parts.append(f"[图片文件: {os.path.basename(image_path)}]")

            # 生成图片描述
            if self.enable_image_description and self.multimodal_llm:
                logger.info(f"正在生成图片描述: {os.path.basename(image_path)}")
                image_description = self._generate_image_description_with_llm(image_path)
                if image_description:
                    content_parts.append(f"图片内容: {image_description}")

                    # 在控制台显示图片描述
                    print(f"\n{'='*60}")
                    print(f"📷 图片: {os.path.basename(image_path)}")
                    print(f"{'='*60}")
                    print(f"🔍 图片描述:")
                    print(f"{image_description}")
                    print(f"{'='*60}\n")
            else:
                # 使用简化描述
                alt_text = image_item.get('alt_text', '')
                if alt_text:
                    content_parts.append(f"图片内容: {alt_text}")
                else:
                    content_parts.append(f"图片内容: 文档配图")

        # 添加OCR文本
        if 'ocr_text' in image_item and image_item['ocr_text'].strip():
            content_parts.append(f"图片中的文字: {image_item['ocr_text']}")

        if not content_parts:
            return None

        content = "\n".join(content_parts)

        metadata = {
            'source': source,
            'page_num': image_item.get('page_num', item_idx + 1),
            'content_type': 'image',
            'image_path': image_item.get('image_path'),
            'alt_text': image_item.get('alt_text', ''),
            'title': image_item.get('title', '')
        }

        return DocumentChunk(content, 'image', metadata)

    def _generate_image_description_with_llm(self, image_path: str) -> str:
        """
        生成详细的图片内容描述（优先使用多模态LLM）

        Args:
            image_path: 图片路径
            ocr_text: OCR识别的文本

        Returns:
            详细的图片内容描述
        """
        try:
            # 首先尝试使用多模态LLM生成详细描述
            llm_description = self._generate_image_caption_with_llm(image_path)

            if llm_description and len(llm_description.strip()) > 20:
                # 如果LLM生成了有效描述，使用它作为主要描述
                enhanced_description = llm_description

                # 如果有OCR文本，作为补充信息添加
                if ocr_text and len(ocr_text.strip()) > 5:
                    cleaned_ocr = ocr_text.strip()[:300]  # 增加OCR文本长度限制
                    enhanced_description += f"\n\n补充OCR文字内容：{cleaned_ocr}"

                return enhanced_description
            else:
                # 如果LLM描述失败，回退到基于规则的描述
                logger.info("多模态LLM描述生成失败，使用基于规则的描述")
                base_description = self._generate_image_description(image_path, ocr_text)

                # 如果有OCR文本，增强描述
                if ocr_text and len(ocr_text.strip()) > 5:
                    cleaned_ocr = ocr_text.strip()[:200]
                    enhanced_description = f"{base_description} 图片中包含的文字内容：{cleaned_ocr}"
                    return enhanced_description

                return base_description

        except Exception as e:
            logger.warning(f"生成详细图片描述失败: {str(e)}")
            return self._generate_image_description(image_path, ocr_text)

    def _generate_image_caption_with_llm(self, image_path: str) -> str:
        """使用多模态LLM生成图像caption"""
        try:
            if not self.multimodal_llm:
                logger.warning("多模态LLM未初始化，使用基于规则的caption生成")
                return ""

            # 使用qwen-vl-max模型分析图像
            return self._call_qwen_vl_for_caption(image_path)

        except Exception as e:
            logger.warning(f"多模态LLM图像分析失败: {str(e)}")
            return ""

    def _call_qwen_vl_for_caption(self, image_path: str) -> str:
        """直接调用Qwen-VL生成caption"""
        try:
            if not self.multimodal_llm:
                logger.warning("多模态LLM未初始化")
                return ""

            if not os.path.exists(image_path):
                logger.error(f"图像文件不存在: {image_path}")
                return ""

            # 导入必要的模块
            from qwen_agent.llm.schema import ContentItem, Message, USER, ASSISTANT

            # 构建详细的图像分析提示词
            prompt = """请详细描述这张图片的内容，包括：
1. 主要对象和场景：描述图片中的主要元素、人物、物体等
2. 文字内容：如果图片中有文字、标题、标签等，请准确识别并记录
3. 图表和数据：如果是图表、表格或技术图形，请描述其类型、数据内容、趋势等
4. 技术细节：如果是技术图、架构图、流程图等，请描述其结构和关键信息
5. 视觉特征：颜色、布局、风格等重要的视觉特征

请用中文回答，内容要准确详细，有助于后续的文档检索和问答。"""

            # 构建多模态消息
            content = [
                ContentItem(image=image_path),
                ContentItem(text=prompt)
            ]

            messages = [Message(USER, content)]

            # 调用多模态LLM
            response = None
            for response in self.multimodal_llm.chat(messages):
                continue

            if response and response[-1].role == ASSISTANT:
                result = response[-1].content.strip()
                logger.info(f"✅ 成功生成图像描述，长度: {len(result)} 字符")

                # 显示描述的前100个字符作为预览
                preview = result[:100] + "..." if len(result) > 100 else result
                logger.info(f"📝 描述预览: {preview}")

                return result
            else:
                logger.warning("❌ 多模态LLM未返回有效响应")
                return ""

        except Exception as e:
            logger.error(f"调用Qwen-VL生成caption失败: {str(e)}")
            return ""

    def _get_api_key(self) -> str:
        """获取API密钥"""
        try:
            # 尝试从多个位置获取API密钥
            key_paths = [
                "dashscope_key.txt",
                "../dashscope_key.txt",
                "../../dashscope_key.txt"
            ]

            for key_path in key_paths:
                if os.path.exists(key_path):
                    with open(key_path, 'r', encoding='utf-8') as f:
                        return f.read().strip()

            # 尝试从环境变量获取
            import os
            return os.environ.get('DASHSCOPE_API_KEY', '')

        except Exception as e:
            logger.warning(f"获取API密钥失败: {str(e)}")
            return ""

    def _generate_image_description(self, image_path: str, ocr_text: str = "") -> str:
        """
        生成图片内容描述

        Args:
            image_path: 图片路径
            ocr_text: OCR识别的文本

        Returns:
            图片内容描述
        """
        try:
            # 基于文件名和路径推断图片类型
            filename = os.path.basename(image_path).lower()

            # 提取图片序号信息
            img_match = re.search(r'img_(\d+)', filename)
            img_number = int(img_match.group(1)) + 1 if img_match else None

            # 基于OCR文本内容推断
            if ocr_text and len(ocr_text.strip()) > 3:
                ocr_lower = ocr_text.lower()
                ocr_snippet = ocr_text.strip()[:100]  # 取前100个字符作为预览

                # 检查是否包含表格特征
                if any(keyword in ocr_lower for keyword in ['table', '表', 'dataset', 'accuracy', 'precision', 'recall', 'f1', '%']):
                    return f"图片{img_number or ''}：实验数据表格，包含性能指标和数值结果。主要内容：{ocr_snippet}..."

                # 检查是否包含图表特征
                elif any(keyword in ocr_lower for keyword in ['figure', 'fig', '图', 'overview', 'architecture', 'framework']):
                    return f"图片{img_number or ''}：技术架构图或系统概览图。主要内容：{ocr_snippet}..."

                # 检查是否包含对比内容
                elif any(keyword in ocr_lower for keyword in ['vs', 'comparison', 'baseline', 'ours', 'proposed']):
                    return f"图片{img_number or ''}：方法对比图表，展示不同模型或方法的性能比较。主要内容：{ocr_snippet}..."

                # 检查是否包含数学公式
                elif any(keyword in ocr_lower for keyword in ['equation', 'formula', '=', '∑', '∏', 'loss', 'objective']):
                    return f"图片{img_number or ''}：数学公式或算法定义。主要内容：{ocr_snippet}..."

                # 检查是否包含流程图特征
                elif any(keyword in ocr_lower for keyword in ['step', 'process', 'flow', 'algorithm', 'training', 'inference']):
                    return f"图片{img_number or ''}：算法流程图或处理步骤示意图。主要内容：{ocr_snippet}..."

                # 如果有OCR文本但不匹配特定类型，直接描述内容
                else:
                    return f"图片{img_number or ''}：包含文字内容的图片。主要内容：{ocr_snippet}..."

            # 基于文件名推断（作为备选）
            if any(keyword in filename for keyword in ['table', 'chart', 'graph']):
                return f"图片{img_number or ''}：表格、图表或图形，包含数据、统计信息或结构化内容。"
            elif any(keyword in filename for keyword in ['figure', 'fig', 'diagram']):
                return f"图片{img_number or ''}：图形或示意图，展示概念、流程或技术架构。"
            elif any(keyword in filename for keyword in ['result', 'experiment', 'test']):
                return f"图片{img_number or ''}：实验结果或测试数据的可视化展示。"
            elif any(keyword in filename for keyword in ['model', 'architecture', 'framework']):
                return f"图片{img_number or ''}：模型架构图或框架示意图，展示系统或算法结构。"
            elif any(keyword in filename for keyword in ['comparison', 'compare', 'vs']):
                return f"图片{img_number or ''}：对比图或比较表，展示不同方法或结果的对比。"
            else:
                # 根据页面位置和图片序号推断
                if 'page_' in filename:
                    page_match = re.search(r'page_(\d+)', filename)
                    if page_match:
                        page_num = int(page_match.group(1))
                        if page_num <= 3:
                            return f"图片{img_number or ''}：文档开头的图片，可能包含标题、摘要或介绍性内容。"
                        elif page_num >= 20:
                            return f"图片{img_number or ''}：文档末尾的图片，可能包含结论、参考文献或附录内容。"
                        else:
                            return f"图片{img_number or ''}：文档第{page_num}页的图片，可能包含主要内容、实验结果或技术细节。"

                return f"图片{img_number or ''}：包含文本、图表、示意图或其他视觉信息的图片。"

        except Exception as e:
            logger.warning(f"生成图片描述失败: {str(e)}")
            return f"图片{img_number or ''}：图片内容需要进一步分析。"

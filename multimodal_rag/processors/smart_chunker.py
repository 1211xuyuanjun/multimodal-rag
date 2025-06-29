"""
简化的智能文档分块器

核心功能：
1. 智能文本分块（保持语义完整性）
2. 图片内容处理（支持LLM描述生成）
3. 表格内容处理
"""

import os
import logging
from typing import List, Dict, Any, Optional

from qwen_agent.llm.schema import ContentItem, Message, USER, ASSISTANT
from qwen_agent.utils.tokenization_qwen import count_tokens

from ..data_structures import ParsedDocument, DocumentChunk
from ..config import DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP

logger = logging.getLogger(__name__)


class SmartChunker:
    """简化的智能文档分块器"""
    
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

    def process_document(self, parsed_doc: ParsedDocument) -> ParsedDocument:
        """
        处理解析后的文档，进行智能分块

        Args:
            parsed_doc: 解析后的文档

        Returns:
            分块后的文档
        """
        try:
            logger.info(f"开始智能分块处理: {parsed_doc.source}")
            
            chunked_doc = ParsedDocument(parsed_doc.source, parsed_doc.doc_type)
            chunked_doc.metadata = parsed_doc.metadata.copy()
            
            # 处理每个页面
            for page_idx, page_data in enumerate(parsed_doc.pages):
                self._process_page(page_data, page_idx, chunked_doc)
            
            logger.info(f"智能分块完成: {len(chunked_doc.chunks)} 个块")
            return chunked_doc
            
        except Exception as e:
            logger.error(f"智能分块处理失败: {str(e)}")
            return parsed_doc

    def _process_page(self, page_data: Dict[str, Any], page_idx: int, chunked_doc: ParsedDocument):
        """处理单个页面"""
        try:
            content_items = page_data.get('content', [])
            
            for item in content_items:
                content_type = item.get('content_type', 'text')
                
                if content_type == 'text':
                    # 处理文本内容
                    text_chunks = self._chunk_text(
                        item.get('text', ''),
                        page_idx,
                        chunked_doc.source
                    )
                    for chunk in text_chunks:
                        chunked_doc.add_chunk(chunk)
                        
                elif content_type == 'image':
                    # 处理图片内容
                    image_chunk = self._create_image_chunk(
                        item,
                        page_idx,
                        chunked_doc.source
                    )
                    if image_chunk:
                        chunked_doc.add_chunk(image_chunk)
                        
                elif content_type == 'table':
                    # 处理表格内容
                    table_chunk = self._create_table_chunk(
                        item,
                        page_idx,
                        chunked_doc.source
                    )
                    if table_chunk:
                        chunked_doc.add_chunk(table_chunk)
                        
        except Exception as e:
            logger.error(f"处理页面失败: {str(e)}")

    def _chunk_text(self, text: str, page_idx: int, source: str) -> List[DocumentChunk]:
        """对文本进行智能分块"""
        if not text.strip():
            return []
            
        # 如果文本很短，直接返回一个块
        if count_tokens(text) <= self.chunk_size:
            metadata = {
                'source': source,
                'page_num': page_idx + 1,
                'chunk_index': 0
            }
            return [DocumentChunk(text, 'text', metadata)]
        
        # 按段落分割文本
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
                    'chunk_index': chunk_index
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
                'chunk_index': chunk_index
            }
            chunks.append(DocumentChunk(current_chunk.strip(), 'text', metadata))
        
        return chunks

    def _create_image_chunk(self, image_item: Dict[str, Any], page_idx: int, source: str) -> Optional[DocumentChunk]:
        """创建图片块"""
        content_parts = []

        # 添加图片基本信息
        if 'image_path' in image_item:
            image_path = image_item['image_path']
            content_parts.append(f"[图片文件: {os.path.basename(image_path)}]")

            # 生成图片描述
            if self.enable_image_description and self.multimodal_llm:
                logger.info(f"正在生成图片描述: {os.path.basename(image_path)}")
                image_description = self._generate_image_description(image_path)
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
            'page_num': page_idx + 1,
            'content_type': 'image',
            'image_path': image_item.get('image_path'),
            'alt_text': image_item.get('alt_text', ''),
            'title': image_item.get('title', '')
        }

        return DocumentChunk(content, 'image', metadata)

    def _create_table_chunk(self, table_item: Dict[str, Any], page_idx: int, source: str) -> Optional[DocumentChunk]:
        """创建表格块"""
        content_parts = []
        
        if 'content' in table_item:
            content_parts.append(f"[表格内容]\n{table_item['content']}")
        
        if not content_parts:
            return None
            
        content = "\n".join(content_parts)
        
        metadata = {
            'source': source,
            'page_num': page_idx + 1,
            'content_type': 'table'
        }
        
        return DocumentChunk(content, 'table', metadata)

    def _generate_image_description(self, image_path: str) -> str:
        """使用多模态LLM生成图像描述"""
        if not self.multimodal_llm:
            logger.warning("多模态LLM未初始化，无法生成图像描述")
            return "图片内容"

        try:
            if not os.path.exists(image_path):
                logger.warning(f"图片文件不存在: {image_path}")
                return "图片内容"

            # 构建多模态消息
            content = [
                ContentItem(image=image_path),
                ContentItem(text="请详细描述这张图片的内容，包括：1. 主要对象和场景；2. 图片中的文字内容；3. 图表、表格或技术图形的具体信息；4. 颜色、布局等视觉特征。请用中文回答，内容要准确详细。")
            ]

            messages = [Message(USER, content)]

            # 调用多模态LLM
            response = None
            for response in self.multimodal_llm.chat(messages):
                continue

            if response and response[-1].role == ASSISTANT:
                result = response[-1].content.strip()
                logger.info(f"✅ 成功生成图像描述，长度: {len(result)} 字符")
                return result
            else:
                logger.warning("❌ 多模态LLM未返回有效响应")
                return "图片内容"

        except Exception as e:
            logger.error(f"调用多模态LLM失败: {str(e)}")
            return "图片内容"

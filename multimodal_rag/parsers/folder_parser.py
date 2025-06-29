"""
文件夹解析器

处理包含Markdown文件和images文件夹的目录结构。
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging

from .markdown_parser import MarkdownParser
from ..data_structures import ParsedDocument, DocumentChunk

logger = logging.getLogger(__name__)


class FolderParser:
    """
    文件夹解析器
    
    功能：
    1. 验证文件夹结构（包含MD文件和images文件夹）
    2. 解析Markdown文件
    3. 处理images文件夹中的图片
    4. 建立MD文件中图片引用与实际图片文件的映射关系
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化文件夹解析器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        
        # 初始化子解析器
        self.markdown_parser = MarkdownParser(config)
        
        # 支持的文件格式
        self.supported_md_extensions = {'.md', '.markdown'}
        self.supported_image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        
    def validate_folder_structure(self, folder_path: str) -> Tuple[bool, str, Optional[str], Optional[str]]:
        """
        验证文件夹结构
        
        Args:
            folder_path: 文件夹路径
            
        Returns:
            (是否有效, 错误信息, MD文件路径, images文件夹路径)
        """
        folder_path = Path(folder_path)
        
        if not folder_path.exists():
            return False, f"文件夹不存在: {folder_path}", None, None
        
        if not folder_path.is_dir():
            return False, f"路径不是文件夹: {folder_path}", None, None
        
        # 查找MD文件
        md_files = []
        for ext in self.supported_md_extensions:
            md_files.extend(list(folder_path.glob(f"*{ext}")))
        
        if not md_files:
            return False, f"文件夹中未找到Markdown文件: {folder_path}", None, None
        
        if len(md_files) > 1:
            logger.warning(f"文件夹中找到多个Markdown文件，将使用第一个: {md_files[0]}")
        
        md_file = md_files[0]
        
        # 查找images文件夹
        images_folder = folder_path / "images"
        if not images_folder.exists():
            logger.warning(f"未找到images文件夹: {images_folder}")
            return True, "", str(md_file), None
        
        if not images_folder.is_dir():
            return False, f"images路径不是文件夹: {images_folder}", None, None
        
        # 检查images文件夹中是否有图片文件
        image_files = []
        for ext in self.supported_image_extensions:
            image_files.extend(list(images_folder.glob(f"*{ext}")))
        
        if not image_files:
            logger.warning(f"images文件夹中未找到图片文件: {images_folder}")
        else:
            logger.info(f"找到 {len(image_files)} 张图片")
        
        return True, "", str(md_file), str(images_folder)
    
    def parse_folder(self, folder_path: str) -> Optional[ParsedDocument]:
        """
        解析文件夹
        
        Args:
            folder_path: 文件夹路径
            
        Returns:
            解析后的文档对象
        """
        try:
            # 验证文件夹结构
            is_valid, error_msg, md_file_path, images_folder_path = self.validate_folder_structure(folder_path)
            
            if not is_valid:
                logger.error(f"文件夹结构验证失败: {error_msg}")
                return None
            
            logger.info(f"开始解析文件夹: {folder_path}")
            logger.info(f"MD文件: {md_file_path}")
            logger.info(f"Images文件夹: {images_folder_path}")
            
            # 解析Markdown文件
            parsed_doc = self.markdown_parser.parse(md_file_path)
            if not parsed_doc:
                logger.error(f"Markdown文件解析失败: {md_file_path}")
                return None
            
            # 处理images文件夹中的图片（只处理被MD文件引用的图片）
            if images_folder_path:
                self._process_referenced_images(parsed_doc, images_folder_path, md_file_path)
            
            logger.info(f"文件夹解析完成: {len(parsed_doc.chunks)} 个文本块, {len(parsed_doc.images)} 张图片")
            
            return parsed_doc
            
        except Exception as e:
            logger.error(f"文件夹解析失败: {str(e)}")
            return None
    
    def _process_referenced_images(self, parsed_doc: ParsedDocument, images_folder_path: str, md_file_path: str):
        """
        只处理在Markdown文件中被引用的图片

        Args:
            parsed_doc: 解析的文档对象
            images_folder_path: images文件夹路径
            md_file_path: MD文件路径
        """
        try:
            # 首先从Markdown内容中提取图片引用
            image_references = self._extract_image_references_from_content(parsed_doc.content)

            if not image_references:
                logger.info("Markdown文件中未找到图片引用，跳过图片处理")
                return

            logger.info(f"找到 {len(image_references)} 个图片引用")

            images_folder = Path(images_folder_path)
            processed_count = 0

            # 只处理被引用的图片
            for ref in image_references:
                try:
                    # 从引用路径中提取文件名
                    ref_filename = Path(ref['image_path']).name

                    # 在images文件夹中查找对应的图片文件
                    image_file = self._find_image_file(images_folder, ref_filename)

                    if image_file:
                        # 创建图片数据
                        image_data = {
                            'image_path': str(image_file),
                            'filename': image_file.name,
                            'relative_path': f"images/{image_file.name}",
                            'source_document': md_file_path,
                            'markdown_reference': ref['image_path'],
                            'alt_text': ref['alt_text'],
                            'title': ref.get('title', ''),
                            'referenced_in_text': True,
                            'width': None,
                            'height': None,
                            'format': image_file.suffix.upper().lstrip('.'),
                            'hash': None
                        }

                        # 添加到文档
                        parsed_doc.add_image(image_data)
                        processed_count += 1

                        logger.debug(f"处理引用图片: {ref_filename} -> {image_file.name}")
                    else:
                        logger.warning(f"未找到引用的图片文件: {ref_filename}")

                except Exception as e:
                    logger.warning(f"处理图片引用失败 {ref}: {str(e)}")

            logger.info(f"成功处理 {processed_count} 张被引用的图片")

        except Exception as e:
            logger.error(f"处理引用图片失败: {str(e)}")
    
    def _extract_image_references_from_content(self, content: str) -> List[Dict[str, str]]:
        """
        从Markdown内容中提取图片引用

        Args:
            content: Markdown内容

        Returns:
            图片引用列表
        """
        image_refs = []

        # Markdown图片语法: ![alt text](image_path "title")
        pattern = r'!\[([^\]]*)\]\(([^)]+)(?:\s+"([^"]*)")?\)'
        matches = re.finditer(pattern, content)

        for match in matches:
            alt_text = match.group(1)
            image_path = match.group(2)
            title = match.group(3) if match.group(3) else ""

            # 只处理指向images文件夹的引用
            if 'images/' in image_path or image_path.startswith('images/'):
                image_refs.append({
                    'alt_text': alt_text,
                    'image_path': image_path,
                    'title': title,
                    'full_match': match.group(0)
                })

        return image_refs

    def _find_image_file(self, images_folder: Path, filename: str) -> Optional[Path]:
        """
        在images文件夹中查找指定的图片文件

        Args:
            images_folder: images文件夹路径
            filename: 要查找的文件名

        Returns:
            找到的图片文件路径，如果未找到则返回None
        """
        # 直接查找文件名匹配的文件
        target_file = images_folder / filename
        if target_file.exists() and target_file.suffix.lower() in self.supported_image_extensions:
            return target_file

        # 如果直接匹配失败，尝试不区分大小写的匹配
        for image_file in images_folder.iterdir():
            if (image_file.is_file() and
                image_file.name.lower() == filename.lower() and
                image_file.suffix.lower() in self.supported_image_extensions):
                return image_file

        return None
    


"""
Markdown解析器

解析Markdown文件，提取文本内容和图片引用。
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from ..data_structures import ParsedDocument, DocumentChunk

logger = logging.getLogger(__name__)

# 检查markdown库是否可用
try:
    import markdown
    from markdown.extensions import codehilite, tables, toc
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False
    logger.warning("markdown库未安装，将使用基础解析")


class MarkdownParser:
    """
    Markdown解析器
    
    功能：
    1. 解析Markdown文件
    2. 提取文本内容
    3. 识别图片引用
    4. 处理代码块、表格等特殊内容
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化Markdown解析器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        
        # 初始化markdown解析器
        if MARKDOWN_AVAILABLE:
            self.md = markdown.Markdown(
                extensions=[
                    'codehilite',
                    'tables',
                    'toc',
                    'fenced_code'
                ],
                extension_configs={
                    'codehilite': {
                        'css_class': 'highlight'
                    },
                    'toc': {
                        'permalink': True
                    }
                }
            )
        else:
            self.md = None
    
    def parse(self, file_path: str) -> Optional[ParsedDocument]:
        """
        解析Markdown文件
        
        Args:
            file_path: Markdown文件路径
            
        Returns:
            解析后的文档对象
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"Markdown文件不存在: {file_path}")
                return None
            
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.info(f"开始解析Markdown文件: {file_path}")
            
            # 创建解析文档对象
            parsed_doc = ParsedDocument(
                source=file_path,
                content=content,
                metadata={
                    'file_type': 'markdown',
                    'file_size': len(content),
                    'encoding': 'utf-8'
                }
            )
            
            # 解析内容
            self._parse_content(parsed_doc, content)
            
            logger.info(f"Markdown解析完成: {len(parsed_doc.pages)} 个页面")
            
            return parsed_doc
            
        except Exception as e:
            logger.error(f"Markdown文件解析失败: {str(e)}")
            return None
    
    def _parse_content(self, parsed_doc: ParsedDocument, content: str):
        """
        解析Markdown内容

        Args:
            parsed_doc: 解析文档对象
            content: Markdown内容
        """
        try:
            # 提取图片引用信息
            image_refs = self.extract_image_references(content)
            if image_refs:
                logger.info(f"找到 {len(image_refs)} 个图片引用")
                # 将图片引用信息添加到文档元数据
                parsed_doc.metadata['image_references'] = image_refs

            # 创建单个页面数据结构，不再预先分块
            # 让SmartChunker统一处理分块逻辑
            page_data = {
                'page_num': 1,
                'content': [{
                    'content_type': 'text',
                    'text': content,
                    'image_references': image_refs,
                    'has_images': len(image_refs) > 0
                }]
            }

            parsed_doc.add_page(page_data)

            # 将图片引用信息保存到文档级别
            parsed_doc.metadata['total_image_references'] = len(image_refs)

        except Exception as e:
            logger.error(f"解析Markdown内容失败: {str(e)}")
    
    def _split_into_sections(self, content: str) -> List[Dict[str, Any]]:
        """
        将Markdown内容按章节分割
        
        Args:
            content: Markdown内容
            
        Returns:
            章节列表
        """
        sections = []
        
        # 按标题分割
        lines = content.split('\n')
        current_section = {
            'title': '',
            'level': 0,
            'content': ''
        }
        
        for line in lines:
            # 检查是否是标题行
            if line.strip().startswith('#'):
                # 保存当前章节
                if current_section['content'].strip():
                    sections.append(current_section.copy())
                
                # 开始新章节
                level = len(line) - len(line.lstrip('#'))
                title = line.lstrip('#').strip()
                
                current_section = {
                    'title': title,
                    'level': level,
                    'content': line + '\n'
                }
            else:
                current_section['content'] += line + '\n'
        
        # 添加最后一个章节
        if current_section['content'].strip():
            sections.append(current_section)
        
        # 如果没有找到章节，将整个内容作为一个章节
        if not sections:
            sections.append({
                'title': 'Document',
                'level': 1,
                'content': content
            })
        
        return sections
    
    def extract_image_references(self, content: str) -> List[Dict[str, str]]:
        """
        提取Markdown中的图片引用
        
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
            
            image_refs.append({
                'alt_text': alt_text,
                'image_path': image_path,
                'title': title,
                'full_match': match.group(0)
            })
        
        return image_refs
    
    def extract_links(self, content: str) -> List[Dict[str, str]]:
        """
        提取Markdown中的链接
        
        Args:
            content: Markdown内容
            
        Returns:
            链接列表
        """
        links = []
        
        # Markdown链接语法: [link text](url "title")
        pattern = r'\[([^\]]+)\]\(([^)]+)(?:\s+"([^"]*)")?\)'
        matches = re.finditer(pattern, content)
        
        for match in matches:
            link_text = match.group(1)
            url = match.group(2)
            title = match.group(3) if match.group(3) else ""
            
            # 排除图片引用
            if not match.group(0).startswith('!'):
                links.append({
                    'text': link_text,
                    'url': url,
                    'title': title,
                    'full_match': match.group(0)
                })
        
        return links
    
    def extract_code_blocks(self, content: str) -> List[Dict[str, str]]:
        """
        提取代码块
        
        Args:
            content: Markdown内容
            
        Returns:
            代码块列表
        """
        code_blocks = []
        
        # 围栏代码块
        pattern = r'```(\w+)?\n(.*?)\n```'
        matches = re.finditer(pattern, content, re.DOTALL)
        
        for match in matches:
            language = match.group(1) if match.group(1) else ""
            code = match.group(2)
            
            code_blocks.append({
                'language': language,
                'code': code,
                'full_match': match.group(0)
            })
        
        # 缩进代码块
        lines = content.split('\n')
        in_code_block = False
        current_code = []
        
        for line in lines:
            if line.startswith('    ') or line.startswith('\t'):
                if not in_code_block:
                    in_code_block = True
                    current_code = []
                current_code.append(line[4:] if line.startswith('    ') else line[1:])
            else:
                if in_code_block and current_code:
                    code_blocks.append({
                        'language': '',
                        'code': '\n'.join(current_code),
                        'full_match': '\n'.join(['    ' + line for line in current_code])
                    })
                    current_code = []
                in_code_block = False
        
        return code_blocks

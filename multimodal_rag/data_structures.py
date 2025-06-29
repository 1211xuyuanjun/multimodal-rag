"""
数据结构定义

包含多模态RAG系统中使用的核心数据结构。
"""

from typing import List, Dict, Any, Optional


class ParsedDocument:
    """解析后的文档数据结构"""
    
    def __init__(self, source: str, content: str = "", metadata: Optional[Dict[str, Any]] = None):
        self.source = source
        self.content = content  # 原始内容
        self.pages: List[Dict[str, Any]] = []
        self.images: List[Dict[str, Any]] = []
        self.tables: List[Dict[str, Any]] = []
        self.chunks: List['DocumentChunk'] = []  # 文档块列表
        self.metadata: Dict[str, Any] = metadata or {}
    
    def add_page(self, page_data: Dict[str, Any]):
        """添加页面数据"""
        self.pages.append(page_data)
    
    def add_image(self, image_data: Dict[str, Any]):
        """添加图片数据"""
        self.images.append(image_data)
    
    def add_table(self, table_data: Dict[str, Any]):
        """添加表格数据"""
        self.tables.append(table_data)
    
    def add_chunk(self, chunk: 'DocumentChunk'):
        """添加文档块"""
        self.chunks.append(chunk)
    
    def get_text_content(self) -> str:
        """获取所有文本内容"""
        if self.content:
            return self.content
        
        # 从页面中提取文本
        text_parts = []
        for page in self.pages:
            for content in page.get('content', []):
                if 'text' in content:
                    text_parts.append(content['text'])
                elif 'table' in content:
                    text_parts.append(content['table'])
        return '\n'.join(text_parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'source': self.source,
            'content': self.content,
            'pages': self.pages,
            'images': self.images,
            'tables': self.tables,
            'chunks': [chunk.to_dict() for chunk in self.chunks],
            'metadata': self.metadata
        }


class DocumentChunk:
    """文档块数据结构"""
    
    def __init__(
        self,
        content: str,
        chunk_type: str = 'text',
        metadata: Optional[Dict[str, Any]] = None,
        token_count: Optional[int] = None
    ):
        self.content = content
        self.chunk_type = chunk_type  # 'text', 'image', 'table'
        self.metadata = metadata or {}
        self.token_count = token_count or self._estimate_token_count(content)
    
    def _estimate_token_count(self, text: str) -> int:
        """估算token数量"""
        # 简单估算：中文按字符数，英文按单词数
        chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
        english_words = len(text.replace('\n', ' ').split()) - chinese_chars
        return chinese_chars + english_words
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'content': self.content,
            'chunk_type': self.chunk_type,
            'metadata': self.metadata,
            'token_count': self.token_count
        }


class ImageData:
    """图片数据结构"""
    
    def __init__(
        self,
        image_path: str,
        filename: str = "",
        description: str = "",
        ocr_text: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.image_path = image_path
        self.filename = filename or self._extract_filename(image_path)
        self.description = description
        self.ocr_text = ocr_text
        self.metadata = metadata or {}
    
    def _extract_filename(self, path: str) -> str:
        """从路径中提取文件名"""
        import os
        return os.path.basename(path)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'image_path': self.image_path,
            'filename': self.filename,
            'description': self.description,
            'ocr_text': self.ocr_text,
            'metadata': self.metadata
        }


class QueryResult:
    """查询结果数据结构"""
    
    def __init__(
        self,
        query: str,
        answer: str,
        sources: List[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.query = query
        self.answer = answer
        self.sources = sources or []
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'query': self.query,
            'answer': self.answer,
            'sources': self.sources,
            'metadata': self.metadata
        }


class ProcessingResult:
    """处理结果数据结构"""
    
    def __init__(
        self,
        success: bool = True,
        message: str = "",
        data: Any = None,
        errors: List[str] = None
    ):
        self.success = success
        self.message = message
        self.data = data
        self.errors = errors or []
    
    def add_error(self, error: str):
        """添加错误信息"""
        self.errors.append(error)
        self.success = False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'success': self.success,
            'message': self.message,
            'data': self.data,
            'errors': self.errors
        }

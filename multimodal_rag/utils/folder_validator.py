"""
文件夹结构验证器

验证输入文件夹是否符合多模态RAG系统的要求。
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class FolderValidator:
    """
    文件夹结构验证器
    
    验证文件夹是否包含：
    1. 一个Markdown文件
    2. 一个images文件夹（可选）
    3. images文件夹中的图片文件（如果存在）
    """
    
    def __init__(self):
        """初始化验证器"""
        self.supported_md_extensions = {'.md', '.markdown'}
        self.supported_image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    
    def validate_folder(self, folder_path: str) -> Dict[str, any]:
        """
        验证文件夹结构
        
        Args:
            folder_path: 文件夹路径
            
        Returns:
            验证结果字典
        """
        result = {
            'is_valid': False,
            'errors': [],
            'warnings': [],
            'md_file': None,
            'images_folder': None,
            'image_files': [],
            'summary': {}
        }
        
        try:
            folder_path = Path(folder_path)
            
            # 检查文件夹是否存在
            if not folder_path.exists():
                result['errors'].append(f"文件夹不存在: {folder_path}")
                return result
            
            if not folder_path.is_dir():
                result['errors'].append(f"路径不是文件夹: {folder_path}")
                return result
            
            # 验证Markdown文件
            md_validation = self._validate_markdown_files(folder_path)
            result['md_file'] = md_validation['md_file']
            result['errors'].extend(md_validation['errors'])
            result['warnings'].extend(md_validation['warnings'])
            
            # 验证images文件夹
            images_validation = self._validate_images_folder(folder_path)
            result['images_folder'] = images_validation['images_folder']
            result['image_files'] = images_validation['image_files']
            result['warnings'].extend(images_validation['warnings'])
            
            # 验证图片引用
            if result['md_file'] and result['images_folder']:
                ref_validation = self._validate_image_references(
                    result['md_file'], 
                    result['image_files']
                )
                result['warnings'].extend(ref_validation['warnings'])
            
            # 生成摘要
            result['summary'] = self._generate_summary(result)
            
            # 判断是否有效（至少要有MD文件）
            result['is_valid'] = len(result['errors']) == 0 and result['md_file'] is not None
            
            return result
            
        except Exception as e:
            result['errors'].append(f"验证过程中发生错误: {str(e)}")
            return result
    
    def _validate_markdown_files(self, folder_path: Path) -> Dict[str, any]:
        """验证Markdown文件"""
        result = {
            'md_file': None,
            'errors': [],
            'warnings': []
        }
        
        # 查找MD文件
        md_files = []
        for ext in self.supported_md_extensions:
            md_files.extend(list(folder_path.glob(f"*{ext}")))
        
        if not md_files:
            result['errors'].append("未找到Markdown文件")
            return result
        
        if len(md_files) > 1:
            result['warnings'].append(f"找到多个Markdown文件，将使用: {md_files[0].name}")
        
        result['md_file'] = str(md_files[0])
        
        # 检查文件大小
        file_size = md_files[0].stat().st_size
        if file_size == 0:
            result['warnings'].append("Markdown文件为空")
        elif file_size > 10 * 1024 * 1024:  # 10MB
            result['warnings'].append("Markdown文件较大，可能影响处理性能")
        
        return result
    
    def _validate_images_folder(self, folder_path: Path) -> Dict[str, any]:
        """验证images文件夹"""
        result = {
            'images_folder': None,
            'image_files': [],
            'warnings': []
        }
        
        images_folder = folder_path / "images"
        
        if not images_folder.exists():
            result['warnings'].append("未找到images文件夹")
            return result
        
        if not images_folder.is_dir():
            result['warnings'].append("images路径不是文件夹")
            return result
        
        result['images_folder'] = str(images_folder)
        
        # 查找图片文件
        image_files = []
        for ext in self.supported_image_extensions:
            image_files.extend(list(images_folder.glob(f"*{ext}")))
        
        if not image_files:
            result['warnings'].append("images文件夹中未找到图片文件")
        else:
            result['image_files'] = [str(f) for f in image_files]
            
            # 检查图片文件大小
            large_files = []
            for img_file in image_files:
                size_mb = img_file.stat().st_size / (1024 * 1024)
                if size_mb > 10:  # 10MB
                    large_files.append(f"{img_file.name} ({size_mb:.1f}MB)")
            
            if large_files:
                result['warnings'].append(f"发现较大的图片文件: {', '.join(large_files)}")
        
        return result
    
    def _validate_image_references(self, md_file: str, image_files: List[str]) -> Dict[str, any]:
        """验证图片引用"""
        result = {
            'warnings': []
        }
        
        try:
            # 读取MD文件内容
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取图片引用
            import re
            pattern = r'!\[.*?\]\((.*?)\)'
            references = re.findall(pattern, content)
            
            # 过滤images文件夹的引用
            image_refs = [ref for ref in references if 'images/' in ref]
            
            if not image_refs:
                result['warnings'].append("Markdown文件中未找到图片引用")
                return result
            
            # 检查引用的图片是否存在
            image_filenames = [Path(f).name for f in image_files]
            
            missing_refs = []
            for ref in image_refs:
                ref_filename = Path(ref).name
                if ref_filename not in image_filenames:
                    missing_refs.append(ref)
            
            if missing_refs:
                result['warnings'].append(f"引用的图片文件不存在: {', '.join(missing_refs)}")
            
            # 检查未被引用的图片（提示信息）
            referenced_filenames = [Path(ref).name for ref in image_refs]
            unused_images = [name for name in image_filenames if name not in referenced_filenames]

            if unused_images:
                result['warnings'].append(f"未被引用的图片文件（将被跳过处理）: {', '.join(unused_images[:5])}" +
                                        (f" 等{len(unused_images)}个文件" if len(unused_images) > 5 else ""))
        
        except Exception as e:
            result['warnings'].append(f"验证图片引用时发生错误: {str(e)}")
        
        return result
    
    def _generate_summary(self, result: Dict[str, any]) -> Dict[str, any]:
        """生成验证摘要"""
        summary = {
            'has_markdown': result['md_file'] is not None,
            'has_images_folder': result['images_folder'] is not None,
            'image_count': len(result['image_files']),
            'error_count': len(result['errors']),
            'warning_count': len(result['warnings'])
        }
        
        if result['md_file']:
            summary['markdown_file'] = Path(result['md_file']).name
        
        return summary
    
    def print_validation_result(self, result: Dict[str, any]):
        """打印验证结果"""
        print("=" * 60)
        print("文件夹结构验证结果")
        print("=" * 60)
        
        # 基本信息
        summary = result['summary']
        print(f"✓ Markdown文件: {'是' if summary['has_markdown'] else '否'}")
        if summary['has_markdown']:
            print(f"  文件名: {summary['markdown_file']}")
        
        print(f"✓ Images文件夹: {'是' if summary['has_images_folder'] else '否'}")
        print(f"✓ 图片数量: {summary['image_count']}")
        
        # 错误信息
        if result['errors']:
            print(f"\n❌ 错误 ({len(result['errors'])}):")
            for error in result['errors']:
                print(f"  - {error}")
        
        # 警告信息
        if result['warnings']:
            print(f"\n⚠️  警告 ({len(result['warnings'])}):")
            for warning in result['warnings']:
                print(f"  - {warning}")
        
        # 验证结果
        print(f"\n结果: {'✅ 通过验证' if result['is_valid'] else '❌ 验证失败'}")
        print("=" * 60)

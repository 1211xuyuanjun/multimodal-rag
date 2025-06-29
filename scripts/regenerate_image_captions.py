#!/usr/bin/env python3
"""
重新生成图像caption的脚本

该脚本会：
1. 读取已存储的图像数据
2. 使用Qwen-VL为每张图像生成详细的caption
3. 更新数据库中的图像描述
"""

import os
import sys
import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

from qwen_agent.llm import get_chat_model
from qwen_agent.llm.schema import ContentItem, Message, USER, ASSISTANT

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageCaptionRegenerator:
    """图像caption重新生成器"""
    
    def __init__(self, storage_path: str = "./webui_storage"):
        self.storage_path = storage_path
        self.db_path = os.path.join(storage_path, "metadata", "metadata.db")
        self.llm = None
        self._init_llm()
    
    def _init_llm(self):
        """初始化多模态LLM"""
        try:
            # 获取API密钥
            api_key = self._get_api_key()
            if not api_key:
                logger.error("未找到API密钥，无法初始化多模态LLM")
                return
            
            # 创建多模态模型
            self.llm = get_chat_model({
                'model': 'qwen-vl-plus',
                'api_key': api_key,
                'model_server': 'dashscope'
            })
            logger.info("多模态LLM初始化成功")
            
        except Exception as e:
            logger.error(f"多模态LLM初始化失败: {str(e)}")
    
    def _get_api_key(self) -> str:
        """获取API密钥"""
        try:
            key_paths = [
                "dashscope_key.txt",
                "../dashscope_key.txt",
                "../../dashscope_key.txt"
            ]
            
            for key_path in key_paths:
                if os.path.exists(key_path):
                    with open(key_path, 'r', encoding='utf-8') as f:
                        return f.read().strip()
            
            return os.environ.get('DASHSCOPE_API_KEY', '')
            
        except Exception as e:
            logger.warning(f"获取API密钥失败: {str(e)}")
            return ""
    
    def get_image_records(self) -> List[Dict[str, Any]]:
        """获取所有图像记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, content, metadata_json 
                FROM metadata 
                WHERE chunk_type = 'image'
                ORDER BY page_num, chunk_index
            ''')
            
            records = []
            for row in cursor.fetchall():
                record_id, content, metadata_json = row
                metadata = json.loads(metadata_json)
                records.append({
                    'id': record_id,
                    'content': content,
                    'metadata': metadata
                })
            
            conn.close()
            logger.info(f"找到 {len(records)} 个图像记录")
            return records
            
        except Exception as e:
            logger.error(f"获取图像记录失败: {str(e)}")
            return []
    
    def generate_caption(self, image_path: str) -> str:
        """为图像生成caption"""
        if not self.llm:
            return ""
        
        try:
            if not os.path.exists(image_path):
                logger.warning(f"图像文件不存在: {image_path}")
                return ""
            
            # 构建多模态消息
            content = [
                ContentItem(image=image_path),
                ContentItem(text="""请详细描述这张图片的内容，包括：
1. 图片类型（表格、图表、流程图、示意图、公式等）
2. 主要内容和信息
3. 关键数据、文字或标签
4. 图片在文档中的作用和意义

请用中文回答，描述要具体详细，不超过200字。""")
            ]
            
            messages = [Message(USER, content)]
            
            # 调用模型
            response = None
            for response in self.llm.chat(messages):
                continue
            
            if response and response[-1].role == ASSISTANT:
                caption = response[-1].content.strip()
                logger.info(f"成功生成caption: {caption[:50]}...")
                return caption
            
            return ""
            
        except Exception as e:
            logger.error(f"生成caption失败: {str(e)}")
            return ""
    
    def update_image_record(self, record_id: str, new_content: str, new_metadata: Dict[str, Any]):
        """更新图像记录"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 更新记录
            cursor.execute('''
                UPDATE metadata 
                SET content = ?, metadata_json = ?
                WHERE id = ?
            ''', (new_content, json.dumps(new_metadata, ensure_ascii=False), record_id))
            
            conn.commit()
            conn.close()
            logger.info(f"成功更新记录: {record_id}")
            
        except Exception as e:
            logger.error(f"更新记录失败: {str(e)}")
    
    def regenerate_all_captions(self):
        """重新生成所有图像的caption"""
        if not self.llm:
            logger.error("多模态LLM未初始化，无法生成caption")
            return
        
        records = self.get_image_records()
        if not records:
            logger.info("没有找到图像记录")
            return
        
        success_count = 0
        total_count = len(records)
        
        for i, record in enumerate(records):
            logger.info(f"处理图像 {i+1}/{total_count}: {record['id']}")
            
            # 获取图像路径
            image_path = record['metadata'].get('image_path')
            if not image_path:
                logger.warning(f"记录 {record['id']} 没有图像路径")
                continue
            
            # 生成新的caption
            caption = self.generate_caption(image_path)
            if not caption:
                logger.warning(f"无法为图像生成caption: {image_path}")
                continue
            
            # 更新内容
            old_content = record['content']
            content_lines = old_content.split('\n')
            
            # 替换图片内容行
            new_content_lines = []
            for line in content_lines:
                if line.startswith('图片内容:'):
                    new_content_lines.append(f"图片内容: {caption}")
                else:
                    new_content_lines.append(line)
            
            # 如果没有图片内容行，添加一行
            if not any(line.startswith('图片内容:') for line in content_lines):
                # 在文件名行后添加
                for j, line in enumerate(new_content_lines):
                    if line.startswith('[图片文件:'):
                        new_content_lines.insert(j+1, f"图片内容: {caption}")
                        break
            
            new_content = '\n'.join(new_content_lines)
            
            # 更新元数据
            new_metadata = record['metadata'].copy()
            new_metadata['image_caption'] = caption
            new_metadata['caption_generated'] = True
            
            # 更新数据库
            self.update_image_record(record['id'], new_content, new_metadata)
            success_count += 1
            
            logger.info(f"成功更新图像 {i+1}/{total_count}")
        
        logger.info(f"caption重新生成完成: {success_count}/{total_count} 成功")

def main():
    """主函数"""
    print("🎨 图像Caption重新生成工具")
    print("=" * 50)
    
    regenerator = ImageCaptionRegenerator()
    
    if not regenerator.llm:
        print("❌ 多模态LLM初始化失败，请检查API密钥配置")
        return
    
    print("🚀 开始重新生成图像caption...")
    regenerator.regenerate_all_captions()
    print("✅ 处理完成！")

if __name__ == "__main__":
    main()

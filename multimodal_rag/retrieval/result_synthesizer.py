"""
结果汇总器

将多个子查询的结果整合成完整、连贯的答案。
"""

import os
import sys
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

# 添加Qwen-Agent到路径
sys.path.append(str(Path(__file__).parent.parent.parent / "Qwen-Agent"))

from qwen_agent.llm.base import BaseChatModel
from qwen_agent.llm.schema import Message, USER, ASSISTANT

from .intelligent_query_decomposer import DecompositionResult

logger = logging.getLogger(__name__)

class ResultSynthesizer:
    """
    结果汇总器
    
    功能：
    1. 多结果整合 - 将多个子查询结果整合
    2. 逻辑连贯性 - 确保答案逻辑连贯
    3. 信息去重 - 去除重复信息
    4. 答案生成 - 生成完整的最终答案
    """
    
    def __init__(
        self,
        llm: Optional[BaseChatModel] = None,
        multimodal_llm: Optional[BaseChatModel] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化结果汇总器

        Args:
            llm: 语言模型
            multimodal_llm: 多模态语言模型
            config: 配置参数
        """
        self.llm = llm
        self.multimodal_llm = multimodal_llm
        self.config = config or {
            'max_synthesis_length': 2000,  # 最大汇总长度
            'enable_logical_flow': True,  # 启用逻辑流程
            'include_source_references': True,  # 包含来源引用
            'synthesis_style': 'comprehensive',  # 汇总风格: 'comprehensive', 'concise', 'structured'
        }
    
    def synthesize_results(
        self,
        original_query: str,
        decomposition: DecompositionResult,
        sub_results: Dict[int, List[Dict[str, Any]]]
    ) -> str:
        """
        汇总多个子查询结果
        
        Args:
            original_query: 原始查询
            decomposition: 查询分解结果
            sub_results: 子查询结果字典 {查询索引: 结果列表}
            
        Returns:
            汇总后的完整答案
        """
        logger.info(f"开始汇总结果，原始查询: {original_query[:50]}...")
        
        if not sub_results:
            return "抱歉，没有找到相关信息。"
        
        # 如果只有一个子查询，直接生成答案
        if len(sub_results) == 1:
            results = list(sub_results.values())[0]
            return self._generate_simple_answer(original_query, results)
        
        # 多子查询结果汇总
        if self.llm:
            return self._llm_synthesize(original_query, decomposition, sub_results)
        else:
            return self._rule_based_synthesize(original_query, decomposition, sub_results)
    
    def _llm_synthesize(
        self,
        original_query: str,
        decomposition: DecompositionResult,
        sub_results: Dict[int, List[Dict[str, Any]]]
    ) -> str:
        """
        使用LLM进行结果汇总
        
        Args:
            original_query: 原始查询
            decomposition: 查询分解结果
            sub_results: 子查询结果
            
        Returns:
            汇总答案
        """
        try:
            # 构建汇总提示
            prompt = self._build_synthesis_prompt(original_query, decomposition, sub_results)
            
            messages = [Message(USER, prompt)]
            
            response = None
            for response in self.llm.chat(messages):
                continue
            
            if response and response[-1].role == ASSISTANT:
                answer = response[-1].content.strip()
                
                # 后处理答案
                answer = self._post_process_answer(answer)
                
                logger.info("LLM汇总完成")
                return answer
        
        except Exception as e:
            logger.error(f"LLM汇总失败: {str(e)}")
        
        # 回退到规则汇总
        return self._rule_based_synthesize(original_query, decomposition, sub_results)
    
    def _build_synthesis_prompt(
        self,
        original_query: str,
        decomposition: DecompositionResult,
        sub_results: Dict[int, List[Dict[str, Any]]]
    ) -> str:
        """
        构建汇总提示
        
        Args:
            original_query: 原始查询
            decomposition: 查询分解结果
            sub_results: 子查询结果
            
        Returns:
            汇总提示文本
        """
        prompt_parts = [
            f"请基于以下多个子查询的结果，为原始问题提供一个完整、连贯的答案。",
            f"",
            f"原始问题：{original_query}",
            f"",
            f"查询分解和结果："
        ]
        
        # 按执行顺序添加子查询结果
        for i, query_idx in enumerate(decomposition.execution_plan):
            if query_idx in sub_results and query_idx < len(decomposition.sub_queries):
                sub_query = decomposition.sub_queries[query_idx]
                results = sub_results[query_idx]
                
                prompt_parts.append(f"")
                prompt_parts.append(f"子查询 {i+1}：{sub_query.query}")
                prompt_parts.append(f"目的：{sub_query.intent}")
                
                if results:
                    prompt_parts.append(f"相关信息：")
                    for j, result in enumerate(results[:3]):  # 最多3个结果
                        content = result.get('content', '')[:300]  # 限制长度
                        if content:
                            prompt_parts.append(f"  {j+1}. {content}")
                else:
                    prompt_parts.append(f"相关信息：未找到相关内容")
        
        # 添加汇总要求
        style_instructions = {
            'comprehensive': "请提供详细、全面的答案，涵盖所有相关方面。",
            'concise': "请提供简洁、要点明确的答案。",
            'structured': "请提供结构化的答案，使用清晰的段落和要点。"
        }
        
        style = self.config.get('synthesis_style', 'comprehensive')
        
        prompt_parts.extend([
            f"",
            f"汇总要求：",
            f"1. {style_instructions.get(style, style_instructions['comprehensive'])}",
            f"2. 确保答案逻辑连贯，各部分之间有清晰的关联",
            f"3. 避免重复信息，整合相似内容",
            f"4. 如果某些子查询没有找到相关信息，请在答案中说明",
            f"5. 保持客观、准确，基于提供的信息回答",
            f"",
            f"请生成完整的答案："
        ])
        
        return "\n".join(prompt_parts)
    
    def _rule_based_synthesize(
        self,
        original_query: str,
        decomposition: DecompositionResult,
        sub_results: Dict[int, List[Dict[str, Any]]]
    ) -> str:
        """
        基于规则的结果汇总
        
        Args:
            original_query: 原始查询
            decomposition: 查询分解结果
            sub_results: 子查询结果
            
        Returns:
            汇总答案
        """
        answer_parts = []
        
        # 根据查询类型选择汇总策略
        if decomposition.intent.intent_type == 'comparative':
            answer_parts = self._synthesize_comparative_results(decomposition, sub_results)
        elif decomposition.intent.intent_type == 'multi_aspect':
            answer_parts = self._synthesize_multi_aspect_results(decomposition, sub_results)
        else:
            answer_parts = self._synthesize_general_results(decomposition, sub_results)
        
        # 组合答案
        if answer_parts:
            answer = "\n\n".join(answer_parts)
        else:
            answer = "抱歉，没有找到相关信息来回答您的问题。"
        
        return answer
    
    def _synthesize_comparative_results(
        self,
        decomposition: DecompositionResult,
        sub_results: Dict[int, List[Dict[str, Any]]]
    ) -> List[str]:
        """汇总比较类结果"""
        parts = []
        
        # 分别描述比较对象
        for i, query_idx in enumerate(decomposition.execution_plan[:-1]):  # 排除最后的比较查询
            if query_idx in sub_results:
                sub_query = decomposition.sub_queries[query_idx]
                results = sub_results[query_idx]
                
                if results:
                    content = self._extract_key_content(results)
                    parts.append(f"关于{sub_query.intent}：{content}")
        
        # 添加比较分析
        if decomposition.execution_plan and decomposition.execution_plan[-1] in sub_results:
            comparison_results = sub_results[decomposition.execution_plan[-1]]
            if comparison_results:
                comparison_content = self._extract_key_content(comparison_results)
                parts.append(f"比较分析：{comparison_content}")
        
        return parts
    
    def _synthesize_multi_aspect_results(
        self,
        decomposition: DecompositionResult,
        sub_results: Dict[int, List[Dict[str, Any]]]
    ) -> List[str]:
        """汇总多方面结果"""
        parts = []
        
        for query_idx in decomposition.execution_plan:
            if query_idx in sub_results and query_idx < len(decomposition.sub_queries):
                sub_query = decomposition.sub_queries[query_idx]
                results = sub_results[query_idx]
                
                if results:
                    content = self._extract_key_content(results)
                    parts.append(f"{sub_query.intent}：{content}")
        
        return parts
    
    def _synthesize_general_results(
        self,
        decomposition: DecompositionResult,
        sub_results: Dict[int, List[Dict[str, Any]]]
    ) -> List[str]:
        """汇总一般结果"""
        parts = []
        
        for query_idx in decomposition.execution_plan:
            if query_idx in sub_results:
                results = sub_results[query_idx]
                if results:
                    content = self._extract_key_content(results)
                    parts.append(content)
        
        return parts
    
    def _extract_key_content(self, results: List[Dict[str, Any]]) -> str:
        """提取关键内容"""
        if not results:
            return "未找到相关信息"
        
        # 合并前几个结果的内容
        contents = []
        for result in results[:2]:  # 最多取前2个结果
            content = result.get('content', '')
            if content:
                # 限制长度并清理格式
                content = content[:200].strip()
                if content:
                    contents.append(content)
        
        return "；".join(contents) if contents else "未找到相关信息"
    
    def _generate_simple_answer(self, query: str, results: List[Dict[str, Any]]) -> str:
        """生成简单答案"""
        if not results:
            return "抱歉，没有找到相关信息。"

        if self.llm:
            # 使用LLM生成更好的答案
            return self._llm_generate_simple_answer(query, results)
        else:
            # 回退到规则方法
            return self._rule_generate_simple_answer(results)

    def _llm_generate_simple_answer(self, query: str, results: List[Dict[str, Any]]) -> str:
        """使用LLM生成简单答案"""
        try:
            # 检查是否是图像相关查询
            if self._is_image_query(query):
                return self._handle_image_query(query, results)

            # 构建上下文
            context_parts = []
            for i, result in enumerate(results[:5]):  # 最多5个结果
                content = result.get('content', '').strip()
                if content:
                    context_parts.append(f"[参考{i+1}] {content}")

            if not context_parts:
                return "抱歉，没有找到相关信息。"

            context = "\n\n".join(context_parts)

            prompt = f"""请基于以下参考资料回答问题：

参考资料：
{context}

问题：{query}

要求：
1. 基于参考资料提供准确、完整的回答
2. 回答要清晰、连贯，避免片段式表达
3. 如果是数据相关问题，请列出具体数据和信息
4. 如果是概念性问题，请提供清晰的解释
5. 不要编造信息，只基于参考资料回答

请提供完整的回答："""

            messages = [Message(USER, prompt)]

            response = None
            for response in self.llm.chat(messages):
                continue

            if response and response[-1].role == ASSISTANT:
                answer = response[-1].content.strip()
                return self._post_process_answer(answer)
            else:
                return self._rule_generate_simple_answer(results)

        except Exception as e:
            logger.error(f"LLM简单答案生成失败: {str(e)}")
            return self._rule_generate_simple_answer(results)

    def _is_image_query(self, query: str) -> bool:
        """判断是否是图像相关查询"""
        image_keywords = [
            '图片', '图像', '照片', '图表', '图形', '示意图', '流程图',
            '第一张', '第二张', '第三张', '最后一张',
            'image', 'picture', 'figure', 'chart', 'diagram'
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in image_keywords)

    def _handle_image_query(self, query: str, results: List[Dict[str, Any]]) -> str:
        """处理图像相关查询"""
        try:
            # 筛选图像结果
            image_results = [r for r in results if r.get('chunk_type') == 'image' or 'image' in r.get('content', '').lower()]

            if not image_results:
                return "抱歉，没有找到相关的图像信息。"

            # 使用图片caption代替直接分析图像
            return self._analyze_images_with_caption(query, image_results)

        except Exception as e:
            logger.error(f"图像查询处理失败: {str(e)}")
            return self._describe_images_basic(query, image_results)

    def _analyze_images_with_caption(self, query: str, image_results: List[Dict[str, Any]]) -> str:
        """使用增强的图片描述分析图像查询"""
        try:
            from qwen_agent.llm.schema import Message, USER, ASSISTANT

            # 基于增强的图像描述回答用户问题
            context_parts = []
            context_parts.append(f"用户问题：{query}")
            context_parts.append("\n基于以下详细的图像信息回答：")

            for i, result in enumerate(image_results[:5]):  # 最多使用5张图
                content = result.get('content', '')
                image_path = result.get('image_path', '')
                llm_description = result.get('llm_description', '')
                ocr_text = result.get('ocr_text', '')

                if content or llm_description:
                    # 提取图像文件名
                    filename = os.path.basename(image_path) if image_path else f"图像{i+1}"

                    # 构建详细的图像信息
                    image_info = f"\n【{filename}】"

                    # 优先使用LLM生成的详细描述
                    if llm_description and len(llm_description.strip()) > 20:
                        image_info += f"\n详细描述：{llm_description}"
                    elif content:
                        image_info += f"\n内容描述：{content}"

                    # 添加OCR文本信息
                    if ocr_text and len(ocr_text.strip()) > 3:
                        image_info += f"\n文字内容：{ocr_text}"

                    # 添加图像路径信息（便于用户理解图像位置）
                    if image_path:
                        image_info += f"\n图像位置：{os.path.basename(image_path)}"

                    context_parts.append(image_info)

            context = "\n".join(context_parts)

            prompt = f"""{context}

要求：
1. 基于上述详细的图像信息回答用户问题
2. 如果用户询问特定图像（如"第一张图片"、"图表"、"表格"等），请提供对应图像的详细信息
3. 充分利用图像的详细描述和文字内容来回答问题
4. 如果图像描述中包含具体数据、技术细节或重要信息，请准确引用
5. 回答要详细、准确，基于已有的图像信息，不要编造内容
6. 如果多张图像相关，请综合分析并说明它们之间的关系

请提供详细、准确的回答："""

            if self.llm:
                messages = [Message(USER, prompt)]
                response = None
                for response in self.llm.chat(messages):
                    continue

                if response and response[-1].role == ASSISTANT:
                    result_text = response[-1].content.strip()
                    logger.info(f"成功生成图像查询回答，长度: {len(result_text)}")
                    return result_text

            # 如果没有LLM，使用基础描述
            return self._describe_images_basic(query, image_results)

        except Exception as e:
            logger.error(f"基于增强描述的图像分析失败: {str(e)}")
            return self._describe_images_basic(query, image_results)

    def _analyze_images_with_llm(self, query: str, image_results: List[Dict[str, Any]]) -> str:
        """使用LLM分析图像（已弃用，使用caption方法代替）"""
        # 直接调用caption方法
        return self._analyze_images_with_caption(query, image_results)



    def _describe_images_basic(self, query: str, image_results: List[Dict[str, Any]]) -> str:
        """基础图像描述"""
        descriptions = []

        for i, result in enumerate(image_results[:3]):
            content = result.get('content', '')

            # 提取图像路径和基本信息
            image_path = result.get('image_path', '')
            if image_path:
                filename = os.path.basename(image_path)
                descriptions.append(f"图像{i+1}（{filename}）：{content}")
            else:
                descriptions.append(f"图像{i+1}：{content}")

        if descriptions:
            intro = "根据文档中的图像信息：\n\n"
            return intro + "\n\n".join(descriptions)
        else:
            return "抱歉，没有找到相关的图像信息。"

    def _rule_generate_simple_answer(self, results: List[Dict[str, Any]]) -> str:
        """基于规则生成简单答案"""
        # 提取并组合内容
        contents = []
        for result in results[:3]:  # 最多3个结果
            content = result.get('content', '').strip()
            if content:
                # 智能截断，保留完整句子
                if len(content) > 500:
                    truncated = content[:500]
                    last_period = truncated.rfind('。')
                    last_dot = truncated.rfind('. ')
                    cut_pos = max(last_period, last_dot)
                    if cut_pos > 300:
                        content = content[:cut_pos + 1]
                    else:
                        content = content[:500] + "..."
                contents.append(content)

        if contents:
            return "\n\n".join(contents)
        else:
            return "抱歉，没有找到相关信息。"
    
    def _post_process_answer(self, answer: str) -> str:
        """后处理答案"""
        # 移除多余的空行
        lines = answer.split('\n')
        cleaned_lines = []
        prev_empty = False
        
        for line in lines:
            line = line.strip()
            if line:
                cleaned_lines.append(line)
                prev_empty = False
            elif not prev_empty:
                cleaned_lines.append('')
                prev_empty = True
        
        # 限制长度
        result = '\n'.join(cleaned_lines)
        if len(result) > self.config['max_synthesis_length']:
            result = result[:self.config['max_synthesis_length']] + "..."
        
        return result

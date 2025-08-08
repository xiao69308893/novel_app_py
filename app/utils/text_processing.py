
# app/utils/text_processing.py
# -*- coding: utf-8 -*-
"""
文本处理工具
提供文本清理、分析、处理功能
"""

import re
import hashlib
from typing import List, Dict, Set, Optional, Tuple, Any
from collections import Counter
import unicodedata
from loguru import logger

try:
    import jieba
    HAS_JIEBA = True
except ImportError:
    HAS_JIEBA = False
    logger.warning("jieba not installed, text segmentation will be limited")


class TextProcessor:
    """文本处理器"""

    def __init__(self):
        """初始化文本处理器"""

        # 敏感词列表（示例）
        self.sensitive_words = {
            "政治敏感词", "违法内容", "不当言论"
            # 实际使用时需要加载完整的敏感词库
        }

        # 停用词列表
        self.stop_words = {
            "的", "了", "在", "是", "我", "有", "和", "就",
            "不", "人", "都", "一", "一个", "上", "也", "很",
            "到", "说", "要", "去", "你", "会", "着", "没有",
            "看", "好", "自己", "这"
        }

    def clean_text(self, text: str) -> str:
        """
        清理文本

        Args:
            text: 原始文本

        Returns:
            str: 清理后的文本
        """

        if not text:
            return ""

        # 去除多余空白字符
        text = re.sub(r'\s+', ' ', text.strip())

        # 去除控制字符
        text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C')

        # 去除HTML标签
        text = re.sub(r'<[^>]+>', '', text)

        # 去除URL
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)

        # 去除邮箱
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)

        # 去除电话号码
        text = re.sub(r'\b\d{3,4}-?\d{7,8}\b', '', text)
        text = re.sub(r'\b1[3-9]\d{9}\b', '', text)

        return text.strip()

    def extract_keywords(
            self,
            text: str,
            top_k: int = 10,
            min_length: int = 2
    ) -> List[Tuple[str, int]]:
        """
        提取关键词

        Args:
            text: 文本内容
            top_k: 返回前k个关键词
            min_length: 最小词长度

        Returns:
            List[Tuple[str, int]]: (关键词, 频次)列表
        """

        try:
            # 清理文本
            clean_text = self.clean_text(text)

            # 分词
            if HAS_JIEBA:
                words = jieba.lcut(clean_text)
            else:
                # 简单的字符级分割（适用于中文）
                words = []
                for i in range(len(clean_text) - min_length + 1):
                    word = clean_text[i:i + min_length]
                    if word.strip():
                        words.append(word)

            # 过滤
            filtered_words = [
                word for word in words
                if len(word) >= min_length
                   and word not in self.stop_words
                   and not word.isdigit()
                   and not re.match(r'^[a-zA-Z]+$', word)
            ]

            # 统计词频
            word_count = Counter(filtered_words)

            # 返回前k个关键词
            return word_count.most_common(top_k)

        except Exception as e:
            logger.error(f"关键词提取失败: {e}")
            return []

    def check_sensitive_words(self, text: str) -> Tuple[bool, List[str]]:
        """
        检查敏感词

        Args:
            text: 文本内容

        Returns:
            Tuple[bool, List[str]]: (是否包含敏感词, 敏感词列表)
        """

        if not text:
            return False, []

        # 转换为小写进行匹配
        text_lower = text.lower()

        found_words = []
        for word in self.sensitive_words:
            if word.lower() in text_lower:
                found_words.append(word)

        return len(found_words) > 0, found_words

    def mask_sensitive_content(
            self,
            text: str,
            mask_char: str = "*"
    ) -> str:
        """
        屏蔽敏感内容

        Args:
            text: 文本内容
            mask_char: 屏蔽字符

        Returns:
            str: 屏蔽后的文本
        """

        if not text:
            return text

        masked_text = text

        for word in self.sensitive_words:
            if word.lower() in text.lower():
                # 替换为等长度的屏蔽字符
                replacement = mask_char * len(word)
                masked_text = re.sub(
                    re.escape(word),
                    replacement,
                    masked_text,
                    flags=re.IGNORECASE
                )

        return masked_text

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        计算文本相似度（简单的Jaccard相似度）

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            float: 相似度 (0-1)
        """

        try:
            # 分词
            if HAS_JIEBA:
                words1 = set(jieba.lcut(self.clean_text(text1)))
                words2 = set(jieba.lcut(self.clean_text(text2)))
            else:
                # 简单的字符级分割
                clean1 = self.clean_text(text1)
                clean2 = self.clean_text(text2)
                words1 = set(clean1[i:i+2] for i in range(len(clean1)-1))
                words2 = set(clean2[i:i+2] for i in range(len(clean2)-1))

            # 去除停用词
            words1 = words1 - self.stop_words
            words2 = words2 - self.stop_words

            # 计算Jaccard相似度
            intersection = len(words1 & words2)
            union = len(words1 | words2)

            if union == 0:
                return 0.0

            return intersection / union

        except Exception as e:
            logger.error(f"相似度计算失败: {e}")
            return 0.0

    def generate_summary(
            self,
            text: str,
            max_length: int = 200
    ) -> str:
        """
        生成文本摘要

        Args:
            text: 原始文本
            max_length: 最大长度

        Returns:
            str: 摘要文本
        """

        try:
            clean_text = self.clean_text(text)

            if len(clean_text) <= max_length:
                return clean_text

            # 简单截断摘要（可以改进为更智能的摘要算法）
            sentences = re.split(r'[。！？.!?]', clean_text)

            summary = ""
            for sentence in sentences:
                if len(summary + sentence) <= max_length - 3:
                    summary += sentence + "。"
                else:
                    break

            if len(summary) > max_length:
                summary = clean_text[:max_length - 3] + "..."

            return summary

        except Exception as e:
            logger.error(f"摘要生成失败: {e}")
            return text[:max_length] if text else ""

    def detect_language(self, text: str) -> str:
        """
        检测文本语言

        Args:
            text: 文本内容

        Returns:
            str: 语言代码 (zh-CN, en-US, etc.)
        """

        if not text:
            return "unknown"

        # 简单的语言检测（可以使用更专业的库如langdetect）
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(re.findall(r'[a-zA-Z]', text))

        if chinese_chars > english_chars:
            return "zh-CN"
        elif english_chars > 0:
            return "en-US"
        else:
            return "unknown"

    def calculate_readability(self, text: str) -> Dict[str, Any]:
        """
        计算文本可读性

        Args:
            text: 文本内容

        Returns:
            Dict[str, Any]: 可读性指标
        """

        try:
            clean_text = self.clean_text(text)

            # 基础统计
            char_count = len(clean_text)
            word_count = len(jieba.lcut(clean_text))
            sentence_count = len(re.split(r'[。！？.!?]', clean_text))

            # 计算指标
            avg_word_length = char_count / word_count if word_count > 0 else 0
            avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0

            # 简单的可读性评分 (1-10, 10最易读)
            readability_score = min(10, max(1, 10 - (avg_sentence_length / 10)))

            return {
                "char_count": char_count,
                "word_count": word_count,
                "sentence_count": sentence_count,
                "avg_word_length": round(avg_word_length, 2),
                "avg_sentence_length": round(avg_sentence_length, 2),
                "readability_score": round(readability_score, 2)
            }

        except Exception as e:
            logger.error(f"可读性计算失败: {e}")
            return {
                "char_count": 0,
                "word_count": 0,
                "sentence_count": 0,
                "avg_word_length": 0,
                "avg_sentence_length": 0,
                "readability_score": 0
            }

    def get_text_hash(self, text: str) -> str:
        """
        获取文本哈希值

        Args:
            text: 文本内容

        Returns:
            str: MD5哈希值
        """

        if not text:
            return ""

        return hashlib.md5(text.encode('utf-8')).hexdigest()


# 全局文本处理器实例
text_processor = TextProcessor()


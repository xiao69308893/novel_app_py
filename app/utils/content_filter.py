# app/utils/content_filter.py
# -*- coding: utf-8 -*-
"""
内容过滤器
用于过滤敏感词汇、垃圾内容等
"""

import re
import asyncio
from typing import List, Set, Optional, Dict, Any
from pathlib import Path
import aiofiles
import logging

logger = logging.getLogger(__name__)


class ContentFilter:
    """内容过滤器"""

    def __init__(self):
        self.sensitive_words: Set[str] = set()
        self.spam_patterns: List[re.Pattern] = []
        self.replacement_char = "*"
        self._initialized = False

    async def initialize(self):
        """初始化过滤器"""
        if self._initialized:
            return

        try:
            # 加载敏感词库
            await self._load_sensitive_words()
            
            # 加载垃圾内容模式
            await self._load_spam_patterns()
            
            self._initialized = True
            logger.info("内容过滤器初始化完成")
        except Exception as e:
            logger.error(f"内容过滤器初始化失败: {e}")

    async def _load_sensitive_words(self):
        """加载敏感词库"""
        # 默认敏感词列表
        default_words = [
            # 政治敏感词
            "法轮功", "六四", "天安门", "达赖", "台独", "藏独", "疆独",
            
            # 色情词汇
            "色情", "黄色", "成人", "性爱", "做爱", "性交", "裸体",
            
            # 暴力词汇
            "杀人", "自杀", "爆炸", "恐怖", "血腥", "暴力", "仇杀",
            
            # 赌博词汇
            "赌博", "博彩", "彩票", "赌场", "老虎机", "百家乐",
            
            # 毒品词汇
            "毒品", "大麻", "海洛因", "冰毒", "摇头丸", "吸毒",
            
            # 诈骗词汇
            "诈骗", "传销", "洗钱", "非法集资", "庞氏骗局"
        ]
        
        self.sensitive_words.update(default_words)
        
        # 尝试从文件加载更多敏感词
        sensitive_words_file = Path("data/sensitive_words.txt")
        if sensitive_words_file.exists():
            try:
                async with aiofiles.open(sensitive_words_file, 'r', encoding='utf-8') as f:
                    content = await f.read()
                    words = [word.strip() for word in content.split('\n') if word.strip()]
                    self.sensitive_words.update(words)
                logger.info(f"从文件加载了 {len(words)} 个敏感词")
            except Exception as e:
                logger.warning(f"加载敏感词文件失败: {e}")

    async def _load_spam_patterns(self):
        """加载垃圾内容模式"""
        # 常见垃圾内容模式
        patterns = [
            # 重复字符
            r'(.)\1{4,}',  # 同一字符重复5次以上
            
            # 大量数字
            r'\d{10,}',  # 10位以上连续数字
            
            # 网址模式
            r'https?://[^\s]+',
            r'www\.[^\s]+',
            r'[a-zA-Z0-9]+\.(com|cn|net|org|edu)[^\s]*',
            
            # 联系方式
            r'(?:微信|QQ|qq|电话|手机|联系)[：:]\s*\d+',
            r'(?:加|添加)(?:微信|QQ|qq)[：:]\s*\w+',
            
            # 广告词汇
            r'(?:免费|赚钱|兼职|代理|招聘|投资|理财)',
            r'(?:点击|访问|下载|注册|登录).{0,10}(?:链接|网址|网站)',
            
            # 刷屏内容
            r'(.{1,10})\1{3,}',  # 短语重复4次以上
        ]
        
        self.spam_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]

    async def filter_text(self, text: str) -> Optional[str]:
        """
        过滤文本内容
        
        Args:
            text: 原始文本
            
        Returns:
            Optional[str]: 过滤后的文本，如果内容不合规则返回None
        """
        if not self._initialized:
            await self.initialize()

        if not text or not text.strip():
            return None

        # 检查是否包含敏感词
        filtered_text = await self._filter_sensitive_words(text)
        
        # 检查是否为垃圾内容
        if await self._is_spam_content(filtered_text):
            return None
            
        # 检查内容质量
        if not await self._check_content_quality(filtered_text):
            return None

        return filtered_text

    async def _filter_sensitive_words(self, text: str) -> str:
        """过滤敏感词"""
        filtered_text = text
        
        for word in self.sensitive_words:
            if word in filtered_text:
                replacement = self.replacement_char * len(word)
                filtered_text = filtered_text.replace(word, replacement)
                
        return filtered_text

    async def _is_spam_content(self, text: str) -> bool:
        """检查是否为垃圾内容"""
        for pattern in self.spam_patterns:
            if pattern.search(text):
                return True
                
        # 检查重复内容比例
        if await self._check_repetition_ratio(text) > 0.6:
            return True
            
        return False

    async def _check_repetition_ratio(self, text: str) -> float:
        """检查重复内容比例"""
        if len(text) < 10:
            return 0.0
            
        # 统计字符频率
        char_count = {}
        for char in text:
            if char.isalnum() or char in '，。！？；：':
                char_count[char] = char_count.get(char, 0) + 1
        
        if not char_count:
            return 0.0
            
        # 计算最高频字符的比例
        max_count = max(char_count.values())
        total_chars = sum(char_count.values())
        
        return max_count / total_chars

    async def _check_content_quality(self, text: str) -> bool:
        """检查内容质量"""
        # 长度检查
        if len(text.strip()) < 2:
            return False
            
        # 检查是否全是标点符号
        alphanumeric_count = sum(1 for char in text if char.isalnum())
        if alphanumeric_count == 0:
            return False
            
        # 检查是否全是数字
        if text.strip().isdigit():
            return False
            
        return True

    async def check_username(self, username: str) -> bool:
        """检查用户名是否合规"""
        if not self._initialized:
            await self.initialize()

        if not username or len(username.strip()) < 2:
            return False
            
        # 检查敏感词
        for word in self.sensitive_words:
            if word in username.lower():
                return False
                
        # 检查特殊字符
        if re.search(r'[^\w\u4e00-\u9fff]', username):
            return False
            
        return True

    async def check_novel_title(self, title: str) -> bool:
        """检查小说标题是否合规"""
        if not self._initialized:
            await self.initialize()

        if not title or len(title.strip()) < 2:
            return False
            
        # 检查敏感词
        for word in self.sensitive_words:
            if word in title:
                return False
                
        # 检查垃圾内容
        for pattern in self.spam_patterns:
            if pattern.search(title):
                return False
                
        return True

    async def get_risk_level(self, text: str) -> Dict[str, Any]:
        """
        获取内容风险等级
        
        Returns:
            Dict包含:
            - level: 风险等级 (low/medium/high)
            - score: 风险分数 (0-100)
            - reasons: 风险原因列表
        """
        if not self._initialized:
            await self.initialize()

        risk_score = 0
        reasons = []

        # 敏感词检查
        sensitive_count = 0
        for word in self.sensitive_words:
            if word in text:
                sensitive_count += 1
                risk_score += 20
                
        if sensitive_count > 0:
            reasons.append(f"包含{sensitive_count}个敏感词")

        # 垃圾内容检查
        spam_matches = 0
        for pattern in self.spam_patterns:
            if pattern.search(text):
                spam_matches += 1
                risk_score += 15
                
        if spam_matches > 0:
            reasons.append(f"匹配{spam_matches}个垃圾内容模式")

        # 重复内容检查
        repetition_ratio = await self._check_repetition_ratio(text)
        if repetition_ratio > 0.4:
            risk_score += int(repetition_ratio * 30)
            reasons.append(f"重复内容比例过高({repetition_ratio:.1%})")

        # 确定风险等级
        if risk_score >= 60:
            level = "high"
        elif risk_score >= 30:
            level = "medium"
        else:
            level = "low"

        return {
            "level": level,
            "score": min(risk_score, 100),
            "reasons": reasons
        }

    async def add_sensitive_word(self, word: str) -> bool:
        """添加敏感词"""
        if word and word.strip():
            self.sensitive_words.add(word.strip())
            return True
        return False

    async def remove_sensitive_word(self, word: str) -> bool:
        """移除敏感词"""
        if word in self.sensitive_words:
            self.sensitive_words.remove(word)
            return True
        return False

    async def get_sensitive_words_count(self) -> int:
        """获取敏感词数量"""
        return len(self.sensitive_words)


# 全局内容过滤器实例
content_filter = ContentFilter()
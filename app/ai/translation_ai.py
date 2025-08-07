# app/ai/translation_ai.py
# -*- coding: utf-8 -*-
"""
翻译AI服务
提供多语言翻译功能
"""

from typing import Dict, Any, List, Optional, Tuple
import asyncio
import json
import logging
from datetime import datetime
import re

from app.ai.base import (
    TranslationService, AIProvider, AIResponse, AIServiceFactory, AIModelType
)

logger = logging.getLogger(__name__)


class MultiLanguageTranslator(TranslationService):
    """多语言翻译器"""
    
    def __init__(self, provider: AIProvider, **kwargs):
        super().__init__(provider, **kwargs)
        
        # 支持的语言映射
        self.supported_languages = {
            "zh": "中文",
            "en": "English",
            "ja": "日本語",
            "ko": "한국어",
            "fr": "Français",
            "de": "Deutsch",
            "es": "Español",
            "ru": "Русский",
            "ar": "العربية",
            "th": "ไทย"
        }
        
        # 语言检测模式
        self.language_patterns = {
            "zh": re.compile(r'[\u4e00-\u9fff]'),
            "ja": re.compile(r'[\u3040-\u309f\u30a0-\u30ff]'),
            "ko": re.compile(r'[\uac00-\ud7af]'),
            "ar": re.compile(r'[\u0600-\u06ff]'),
            "th": re.compile(r'[\u0e00-\u0e7f]'),
            "ru": re.compile(r'[\u0400-\u04ff]')
        }
        
        # 翻译质量评估
        self.quality_thresholds = {
            "excellent": 0.9,
            "good": 0.7,
            "fair": 0.5,
            "poor": 0.3
        }
    
    async def initialize(self) -> bool:
        """初始化翻译服务"""
        try:
            logger.info(f"初始化翻译服务: {self.provider.value}")
            # 这里可以初始化具体的翻译API客户端
            # 例如Google Translate、百度翻译、腾讯翻译等
            return True
        except Exception as e:
            logger.error(f"初始化翻译服务失败: {e}")
            return False
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 简单的翻译测试
            response = await self.translate_text("Hello", "zh", "en")
            return response.success
        except Exception:
            return False
    
    async def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "provider": self.provider.value,
            "model": self.model_name,
            "type": "translation",
            "supported_languages": list(self.supported_languages.keys()),
            "capabilities": ["text_translation", "language_detection", "quality_assessment"]
        }
    
    async def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: str = None,
        **kwargs
    ) -> AIResponse:
        """翻译文本"""
        try:
            # 检测源语言
            if not source_language:
                detected_lang = await self.detect_language(text)
                if detected_lang.success:
                    source_language = detected_lang.data["language"]
                else:
                    source_language = "auto"
            
            # 验证语言支持
            if target_language not in self.supported_languages:
                return self._create_response(
                    success=False,
                    error=f"不支持的目标语言: {target_language}"
                )
            
            # 执行翻译
            translated_text = await self._perform_translation(
                text, source_language, target_language
            )
            
            # 评估翻译质量
            quality_score = await self._assess_translation_quality(
                text, translated_text, source_language, target_language
            )
            
            return self._create_response(
                success=True,
                data={
                    "translated_text": translated_text,
                    "source_language": source_language,
                    "target_language": target_language,
                    "quality_score": quality_score,
                    "quality_level": self._get_quality_level(quality_score),
                    "word_count": len(text.split()),
                    "char_count": len(text)
                }
            )
            
        except Exception as e:
            return self._create_response(
                success=False,
                error=str(e)
            )
    
    async def detect_language(self, text: str) -> AIResponse:
        """检测语言"""
        try:
            # 简单的语言检测逻辑
            detected_languages = {}
            
            for lang_code, pattern in self.language_patterns.items():
                matches = len(pattern.findall(text))
                if matches > 0:
                    detected_languages[lang_code] = matches / len(text)
            
            if detected_languages:
                # 选择匹配度最高的语言
                best_match = max(detected_languages.items(), key=lambda x: x[1])
                detected_language = best_match[0]
                confidence = best_match[1]
            else:
                # 默认检测为英文
                detected_language = "en"
                confidence = 0.5
            
            return self._create_response(
                success=True,
                data={
                    "language": detected_language,
                    "language_name": self.supported_languages.get(detected_language, "Unknown"),
                    "confidence": confidence,
                    "all_detections": detected_languages
                }
            )
            
        except Exception as e:
            return self._create_response(
                success=False,
                error=str(e)
            )
    
    async def get_supported_languages(self) -> AIResponse:
        """获取支持的语言列表"""
        try:
            return self._create_response(
                success=True,
                data={
                    "languages": self.supported_languages,
                    "count": len(self.supported_languages)
                }
            )
        except Exception as e:
            return self._create_response(
                success=False,
                error=str(e)
            )
    
    async def batch_translate(
        self,
        texts: List[str],
        target_language: str,
        source_language: str = None
    ) -> AIResponse:
        """批量翻译"""
        try:
            results = []
            
            for i, text in enumerate(texts):
                try:
                    response = await self.translate_text(
                        text, target_language, source_language
                    )
                    
                    if response.success:
                        results.append({
                            "index": i,
                            "original_text": text,
                            "translated_text": response.data["translated_text"],
                            "quality_score": response.data["quality_score"],
                            "success": True
                        })
                    else:
                        results.append({
                            "index": i,
                            "original_text": text,
                            "error": response.error,
                            "success": False
                        })
                        
                except Exception as e:
                    results.append({
                        "index": i,
                        "original_text": text,
                        "error": str(e),
                        "success": False
                    })
            
            success_count = sum(1 for r in results if r["success"])
            
            return self._create_response(
                success=True,
                data={
                    "results": results,
                    "total_count": len(texts),
                    "success_count": success_count,
                    "failure_count": len(texts) - success_count,
                    "success_rate": success_count / len(texts) if texts else 0
                }
            )
            
        except Exception as e:
            return self._create_response(
                success=False,
                error=str(e)
            )
    
    async def translate_novel_chapter(
        self,
        chapter_content: str,
        target_language: str,
        source_language: str = None,
        preserve_formatting: bool = True
    ) -> AIResponse:
        """翻译小说章节"""
        try:
            # 分段处理长文本
            paragraphs = chapter_content.split('\n\n')
            translated_paragraphs = []
            
            total_quality_score = 0
            paragraph_count = 0
            
            for paragraph in paragraphs:
                if paragraph.strip():
                    response = await self.translate_text(
                        paragraph.strip(), target_language, source_language
                    )
                    
                    if response.success:
                        translated_paragraphs.append(response.data["translated_text"])
                        total_quality_score += response.data["quality_score"]
                        paragraph_count += 1
                    else:
                        # 翻译失败时保留原文
                        translated_paragraphs.append(paragraph.strip())
                else:
                    translated_paragraphs.append("")
            
            # 重新组合文本
            if preserve_formatting:
                translated_content = '\n\n'.join(translated_paragraphs)
            else:
                translated_content = ' '.join(p for p in translated_paragraphs if p)
            
            # 计算平均质量分数
            avg_quality_score = total_quality_score / paragraph_count if paragraph_count > 0 else 0
            
            return self._create_response(
                success=True,
                data={
                    "translated_content": translated_content,
                    "source_language": source_language,
                    "target_language": target_language,
                    "paragraph_count": paragraph_count,
                    "average_quality_score": avg_quality_score,
                    "quality_level": self._get_quality_level(avg_quality_score),
                    "word_count": len(chapter_content.split()),
                    "char_count": len(chapter_content)
                }
            )
            
        except Exception as e:
            return self._create_response(
                success=False,
                error=str(e)
            )
    
    async def _perform_translation(
        self,
        text: str,
        source_language: str,
        target_language: str
    ) -> str:
        """执行实际翻译"""
        # 这里应该调用实际的翻译API
        # 暂时返回模拟翻译结果
        
        if target_language == "zh":
            return f"[中文翻译] {text}"
        elif target_language == "en":
            return f"[English Translation] {text}"
        elif target_language == "ja":
            return f"[日本語翻訳] {text}"
        else:
            return f"[{target_language} Translation] {text}"
    
    async def _assess_translation_quality(
        self,
        original_text: str,
        translated_text: str,
        source_language: str,
        target_language: str
    ) -> float:
        """评估翻译质量"""
        # 简单的质量评估逻辑
        # 实际应用中可以使用BLEU、METEOR等指标
        
        quality_factors = []
        
        # 长度比例检查
        length_ratio = len(translated_text) / len(original_text) if original_text else 0
        if 0.5 <= length_ratio <= 2.0:
            quality_factors.append(0.8)
        else:
            quality_factors.append(0.4)
        
        # 特殊字符保留检查
        original_special = set(re.findall(r'[^\w\s]', original_text))
        translated_special = set(re.findall(r'[^\w\s]', translated_text))
        special_preservation = len(original_special & translated_special) / len(original_special) if original_special else 1.0
        quality_factors.append(special_preservation)
        
        # 基于语言的质量调整
        if source_language == target_language:
            quality_factors.append(1.0)  # 相同语言，质量最高
        elif (source_language, target_language) in [("zh", "en"), ("en", "zh")]:
            quality_factors.append(0.8)  # 中英互译，质量较高
        else:
            quality_factors.append(0.7)  # 其他语言对，质量中等
        
        return sum(quality_factors) / len(quality_factors)
    
    def _get_quality_level(self, quality_score: float) -> str:
        """获取质量等级"""
        for level, threshold in self.quality_thresholds.items():
            if quality_score >= threshold:
                return level
        return "poor"


class NovelTranslationManager:
    """小说翻译管理器"""
    
    def __init__(self, translator: MultiLanguageTranslator):
        self.translator = translator
        self.translation_cache = {}
        self.translation_history = []
    
    async def translate_novel_metadata(
        self,
        novel_data: Dict[str, Any],
        target_language: str
    ) -> Dict[str, Any]:
        """翻译小说元数据"""
        try:
            translated_data = novel_data.copy()
            
            # 翻译标题
            if "title" in novel_data:
                title_response = await self.translator.translate_text(
                    novel_data["title"], target_language
                )
                if title_response.success:
                    translated_data["title"] = title_response.data["translated_text"]
            
            # 翻译简介
            if "description" in novel_data:
                desc_response = await self.translator.translate_text(
                    novel_data["description"], target_language
                )
                if desc_response.success:
                    translated_data["description"] = desc_response.data["translated_text"]
            
            # 翻译标签
            if "tags" in novel_data and isinstance(novel_data["tags"], list):
                translated_tags = []
                for tag in novel_data["tags"]:
                    tag_response = await self.translator.translate_text(tag, target_language)
                    if tag_response.success:
                        translated_tags.append(tag_response.data["translated_text"])
                    else:
                        translated_tags.append(tag)
                translated_data["tags"] = translated_tags
            
            translated_data["translation_language"] = target_language
            translated_data["translation_timestamp"] = datetime.utcnow().isoformat()
            
            return translated_data
            
        except Exception as e:
            logger.error(f"翻译小说元数据失败: {e}")
            return novel_data
    
    async def get_translation_progress(
        self,
        novel_id: int,
        target_language: str
    ) -> Dict[str, Any]:
        """获取翻译进度"""
        try:
            # 这里应该从数据库查询实际的翻译进度
            # 暂时返回模拟数据
            return {
                "novel_id": novel_id,
                "target_language": target_language,
                "total_chapters": 100,
                "translated_chapters": 45,
                "progress_percentage": 45.0,
                "last_updated": datetime.utcnow().isoformat(),
                "quality_average": 0.85,
                "estimated_completion": "2024-02-15"
            }
        except Exception as e:
            logger.error(f"获取翻译进度失败: {e}")
            return {}
    
    async def create_translation_task(
        self,
        novel_id: int,
        target_language: str,
        priority: str = "normal",
        options: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """创建翻译任务"""
        try:
            task_id = f"trans_{novel_id}_{target_language}_{int(datetime.utcnow().timestamp())}"
            
            task = {
                "task_id": task_id,
                "novel_id": novel_id,
                "target_language": target_language,
                "priority": priority,
                "status": "pending",
                "created_at": datetime.utcnow().isoformat(),
                "options": options or {},
                "progress": 0.0
            }
            
            # 这里应该将任务保存到数据库或任务队列
            logger.info(f"创建翻译任务: {task_id}")
            
            return task
            
        except Exception as e:
            logger.error(f"创建翻译任务失败: {e}")
            return {}


# 注册服务到工厂
AIServiceFactory.register_service(
    AIModelType.TRANSLATION,
    AIProvider.LOCAL,
    MultiLanguageTranslator
)
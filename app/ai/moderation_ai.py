# app/ai/moderation_ai.py
# -*- coding: utf-8 -*-
"""
内容审核AI服务
提供内容安全检测、敏感词过滤等功能
"""

from typing import Dict, Any, List, Optional, Set
import asyncio
import json
import logging
import re
from datetime import datetime
from enum import Enum

from app.ai.base import (
    ContentModerationService, AIProvider, AIResponse, AIServiceFactory, AIModelType
)

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """风险等级"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ViolationType(Enum):
    """违规类型"""
    NONE = "none"
    SPAM = "spam"
    HATE_SPEECH = "hate_speech"
    VIOLENCE = "violence"
    SEXUAL_CONTENT = "sexual_content"
    POLITICAL = "political"
    ILLEGAL = "illegal"
    HARASSMENT = "harassment"
    MISINFORMATION = "misinformation"
    COPYRIGHT = "copyright"


class ContentModerator(ContentModerationService):
    """内容审核器"""
    
    def __init__(self, provider: AIProvider, **kwargs):
        super().__init__(provider, **kwargs)
        
        # 敏感词库
        self.sensitive_words = {
            ViolationType.HATE_SPEECH: [
                "仇恨", "歧视", "种族主义", "性别歧视"
            ],
            ViolationType.VIOLENCE: [
                "暴力", "杀害", "伤害", "攻击", "血腥"
            ],
            ViolationType.SEXUAL_CONTENT: [
                "色情", "性行为", "裸体", "成人内容"
            ],
            ViolationType.POLITICAL: [
                "政治敏感", "政府批评", "政治人物"
            ],
            ViolationType.ILLEGAL: [
                "毒品", "赌博", "诈骗", "非法交易"
            ]
        }
        
        # 风险权重
        self.risk_weights = {
            ViolationType.HATE_SPEECH: 0.9,
            ViolationType.VIOLENCE: 0.8,
            ViolationType.SEXUAL_CONTENT: 0.7,
            ViolationType.POLITICAL: 0.9,
            ViolationType.ILLEGAL: 1.0,
            ViolationType.HARASSMENT: 0.8,
            ViolationType.MISINFORMATION: 0.6,
            ViolationType.COPYRIGHT: 0.5,
            ViolationType.SPAM: 0.3
        }
        
        # 正则表达式模式
        self.patterns = {
            "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            "phone": re.compile(r'\b\d{3}-?\d{3,4}-?\d{4}\b'),
            "url": re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'),
            "repeated_chars": re.compile(r'(.)\1{4,}'),  # 连续重复字符
            "excessive_punctuation": re.compile(r'[!?。]{3,}')  # 过多标点
        }
    
    async def initialize(self) -> bool:
        """初始化审核服务"""
        try:
            logger.info(f"初始化内容审核服务: {self.provider.value}")
            # 加载敏感词库
            await self._load_sensitive_words()
            return True
        except Exception as e:
            logger.error(f"初始化审核服务失败: {e}")
            return False
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 简单的审核测试
            response = await self.moderate_content("测试内容", "text")
            return response.success
        except Exception:
            return False
    
    async def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "provider": self.provider.value,
            "model": self.model_name,
            "type": "content_moderation",
            "capabilities": [
                "text_moderation", "image_moderation", "spam_detection",
                "hate_speech_detection", "violence_detection"
            ],
            "supported_violation_types": [vt.value for vt in ViolationType],
            "risk_levels": [rl.value for rl in RiskLevel]
        }
    
    async def moderate_content(
        self,
        content: str,
        content_type: str = "text",
        **kwargs
    ) -> AIResponse:
        """内容审核"""
        try:
            moderation_result = {
                "content_type": content_type,
                "violations": [],
                "risk_level": RiskLevel.SAFE.value,
                "risk_score": 0.0,
                "is_safe": True,
                "details": {}
            }
            
            if content_type == "text":
                result = await self._moderate_text(content)
                moderation_result.update(result)
            elif content_type == "image":
                result = await self._moderate_image(content)
                moderation_result.update(result)
            else:
                return self._create_response(
                    success=False,
                    error=f"不支持的内容类型: {content_type}"
                )
            
            return self._create_response(
                success=True,
                data=moderation_result
            )
            
        except Exception as e:
            return self._create_response(
                success=False,
                error=str(e)
            )
    
    async def detect_spam(self, content: str, **kwargs) -> AIResponse:
        """垃圾内容检测"""
        try:
            spam_indicators = []
            spam_score = 0.0
            
            # 检查重复字符
            if self.patterns["repeated_chars"].search(content):
                spam_indicators.append("excessive_repeated_characters")
                spam_score += 0.3
            
            # 检查过多标点
            if self.patterns["excessive_punctuation"].search(content):
                spam_indicators.append("excessive_punctuation")
                spam_score += 0.2
            
            # 检查联系方式
            if self.patterns["email"].search(content) or self.patterns["phone"].search(content):
                spam_indicators.append("contact_information")
                spam_score += 0.4
            
            # 检查URL
            if self.patterns["url"].search(content):
                spam_indicators.append("external_links")
                spam_score += 0.3
            
            # 检查内容长度和重复度
            if len(content) < 10:
                spam_indicators.append("too_short")
                spam_score += 0.2
            
            # 检查重复词汇
            words = content.split()
            if len(words) > 0:
                unique_words = set(words)
                repetition_ratio = 1 - (len(unique_words) / len(words))
                if repetition_ratio > 0.7:
                    spam_indicators.append("high_word_repetition")
                    spam_score += repetition_ratio * 0.5
            
            # 限制分数在0-1之间
            spam_score = min(spam_score, 1.0)
            
            is_spam = spam_score > 0.5
            
            return self._create_response(
                success=True,
                data={
                    "is_spam": is_spam,
                    "spam_score": spam_score,
                    "spam_indicators": spam_indicators,
                    "confidence": spam_score if is_spam else 1 - spam_score
                }
            )
            
        except Exception as e:
            return self._create_response(
                success=False,
                error=str(e)
            )
    
    async def check_policy_violation(
        self,
        content: str,
        policies: List[str] = None,
        **kwargs
    ) -> AIResponse:
        """策略违规检查"""
        try:
            if not policies:
                policies = ["community_guidelines", "content_policy", "user_agreement"]
            
            violations = []
            violation_details = {}
            
            # 检查各种违规类型
            for violation_type in ViolationType:
                if violation_type == ViolationType.NONE:
                    continue
                
                violation_result = await self._check_specific_violation(content, violation_type)
                if violation_result["detected"]:
                    violations.append({
                        "type": violation_type.value,
                        "confidence": violation_result["confidence"],
                        "evidence": violation_result["evidence"]
                    })
                    violation_details[violation_type.value] = violation_result
            
            # 计算总体风险分数
            total_risk_score = 0.0
            for violation in violations:
                violation_type = ViolationType(violation["type"])
                weight = self.risk_weights.get(violation_type, 0.5)
                total_risk_score += violation["confidence"] * weight
            
            total_risk_score = min(total_risk_score, 1.0)
            
            # 确定风险等级
            risk_level = self._calculate_risk_level(total_risk_score)
            
            return self._create_response(
                success=True,
                data={
                    "violations": violations,
                    "violation_count": len(violations),
                    "risk_score": total_risk_score,
                    "risk_level": risk_level.value,
                    "is_violation": len(violations) > 0,
                    "policies_checked": policies,
                    "details": violation_details
                }
            )
            
        except Exception as e:
            return self._create_response(
                success=False,
                error=str(e)
            )
    
    async def _moderate_text(self, text: str) -> Dict[str, Any]:
        """文本内容审核"""
        violations = []
        risk_score = 0.0
        details = {}
        
        # 检查敏感词
        for violation_type, words in self.sensitive_words.items():
            found_words = []
            for word in words:
                if word in text:
                    found_words.append(word)
            
            if found_words:
                confidence = len(found_words) / len(words)
                violations.append({
                    "type": violation_type.value,
                    "confidence": confidence,
                    "evidence": found_words
                })
                risk_score += confidence * self.risk_weights.get(violation_type, 0.5)
        
        # 垃圾内容检测
        spam_result = await self.detect_spam(text)
        if spam_result.success and spam_result.data["is_spam"]:
            violations.append({
                "type": ViolationType.SPAM.value,
                "confidence": spam_result.data["spam_score"],
                "evidence": spam_result.data["spam_indicators"]
            })
            risk_score += spam_result.data["spam_score"] * 0.3
        
        risk_score = min(risk_score, 1.0)
        risk_level = self._calculate_risk_level(risk_score)
        
        return {
            "violations": violations,
            "risk_level": risk_level.value,
            "risk_score": risk_score,
            "is_safe": risk_level == RiskLevel.SAFE,
            "details": {
                "text_length": len(text),
                "word_count": len(text.split()),
                "sensitive_word_matches": sum(len(v.get("evidence", [])) for v in violations)
            }
        }
    
    async def _moderate_image(self, image_path: str) -> Dict[str, Any]:
        """图片内容审核"""
        # 图片审核的模拟实现
        # 实际应用中需要使用图像识别API
        
        violations = []
        risk_score = 0.1  # 默认低风险
        
        # 模拟图片审核结果
        # 这里可以集成腾讯云、阿里云等图片审核服务
        
        risk_level = self._calculate_risk_level(risk_score)
        
        return {
            "violations": violations,
            "risk_level": risk_level.value,
            "risk_score": risk_score,
            "is_safe": risk_level == RiskLevel.SAFE,
            "details": {
                "image_path": image_path,
                "analysis_method": "simulated"
            }
        }
    
    async def _check_specific_violation(
        self,
        content: str,
        violation_type: ViolationType
    ) -> Dict[str, Any]:
        """检查特定类型的违规"""
        if violation_type in self.sensitive_words:
            words = self.sensitive_words[violation_type]
            found_words = [word for word in words if word in content]
            
            if found_words:
                confidence = len(found_words) / len(words)
                return {
                    "detected": True,
                    "confidence": confidence,
                    "evidence": found_words
                }
        
        return {
            "detected": False,
            "confidence": 0.0,
            "evidence": []
        }
    
    def _calculate_risk_level(self, risk_score: float) -> RiskLevel:
        """计算风险等级"""
        if risk_score >= 0.8:
            return RiskLevel.CRITICAL
        elif risk_score >= 0.6:
            return RiskLevel.HIGH
        elif risk_score >= 0.4:
            return RiskLevel.MEDIUM
        elif risk_score >= 0.2:
            return RiskLevel.LOW
        else:
            return RiskLevel.SAFE
    
    async def _load_sensitive_words(self):
        """加载敏感词库"""
        try:
            # 这里可以从文件或数据库加载敏感词
            # 暂时使用预定义的词库
            logger.info("敏感词库加载完成")
        except Exception as e:
            logger.error(f"加载敏感词库失败: {e}")


class NovelContentModerator:
    """小说内容审核器"""
    
    def __init__(self, moderator: ContentModerator):
        self.moderator = moderator
        self.moderation_history = []
    
    async def moderate_novel_content(
        self,
        novel_id: int,
        content: str,
        content_type: str = "chapter"
    ) -> Dict[str, Any]:
        """审核小说内容"""
        try:
            # 执行内容审核
            moderation_response = await self.moderator.moderate_content(content, "text")
            
            if not moderation_response.success:
                return {
                    "success": False,
                    "error": moderation_response.error
                }
            
            result = moderation_response.data
            
            # 记录审核历史
            moderation_record = {
                "novel_id": novel_id,
                "content_type": content_type,
                "moderation_result": result,
                "timestamp": datetime.utcnow().isoformat(),
                "content_length": len(content)
            }
            
            self.moderation_history.append(moderation_record)
            
            # 根据审核结果决定处理方式
            action = self._determine_action(result)
            
            return {
                "success": True,
                "moderation_result": result,
                "recommended_action": action,
                "moderation_id": len(self.moderation_history)
            }
            
        except Exception as e:
            logger.error(f"审核小说内容失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def batch_moderate_chapters(
        self,
        novel_id: int,
        chapters: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """批量审核章节"""
        try:
            results = []
            
            for chapter in chapters:
                chapter_id = chapter.get("id")
                content = chapter.get("content", "")
                
                if content:
                    result = await self.moderate_novel_content(
                        novel_id, content, "chapter"
                    )
                    result["chapter_id"] = chapter_id
                    results.append(result)
            
            # 统计结果
            total_count = len(results)
            safe_count = sum(1 for r in results if r.get("moderation_result", {}).get("is_safe", False))
            violation_count = total_count - safe_count
            
            return {
                "success": True,
                "results": results,
                "summary": {
                    "total_chapters": total_count,
                    "safe_chapters": safe_count,
                    "violation_chapters": violation_count,
                    "safety_rate": safe_count / total_count if total_count > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"批量审核章节失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _determine_action(self, moderation_result: Dict[str, Any]) -> str:
        """根据审核结果确定处理动作"""
        risk_level = moderation_result.get("risk_level", "safe")
        
        if risk_level == "critical":
            return "block"  # 阻止发布
        elif risk_level == "high":
            return "review"  # 人工审核
        elif risk_level == "medium":
            return "warn"  # 警告用户
        elif risk_level == "low":
            return "monitor"  # 监控
        else:
            return "approve"  # 批准发布


# 注册服务到工厂
AIServiceFactory.register_service(
    AIModelType.CONTENT_MODERATION,
    AIProvider.LOCAL,
    ContentModerator
)
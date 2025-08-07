# app/utils/file_upload.py
# -*- coding: utf-8 -*-
"""
文件上传工具
支持图片上传、文件验证、缩略图生成等功能
"""

import os
import uuid
import hashlib
import mimetypes
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import aiofiles
from PIL import Image, ImageOps
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class FileUploadManager:
    """文件上传管理器"""

    def __init__(self):
        # 配置
        self.upload_dir = Path("static/uploads")
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.max_image_size = 5 * 1024 * 1024   # 5MB
        
        # 允许的文件类型
        self.allowed_image_types = {
            'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'
        }
        self.allowed_document_types = {
            'text/plain', 'application/pdf', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        
        # 图片尺寸配置
        self.thumbnail_sizes = {
            'small': (150, 150),
            'medium': (300, 300),
            'large': (600, 600)
        }
        
        # 确保上传目录存在
        self._ensure_upload_dirs()

    def _ensure_upload_dirs(self):
        """确保上传目录存在"""
        dirs = [
            self.upload_dir,
            self.upload_dir / "images",
            self.upload_dir / "documents",
            self.upload_dir / "avatars",
            self.upload_dir / "covers",
            self.upload_dir / "thumbnails"
        ]
        
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)

    async def upload_image(
        self, 
        file_content: bytes, 
        filename: str,
        category: str = "images",
        generate_thumbnails: bool = True
    ) -> Dict[str, Any]:
        """
        上传图片
        
        Args:
            file_content: 文件内容
            filename: 原始文件名
            category: 分类 (images/avatars/covers)
            generate_thumbnails: 是否生成缩略图
            
        Returns:
            Dict包含上传结果信息
        """
        try:
            # 验证文件
            validation_result = await self._validate_image(file_content, filename)
            if not validation_result['valid']:
                return validation_result

            # 生成文件信息
            file_info = await self._generate_file_info(filename, category)
            
            # 保存原图
            original_path = await self._save_file(file_content, file_info['path'])
            
            result = {
                'success': True,
                'filename': file_info['filename'],
                'original_path': str(original_path),
                'url': f"/static/uploads/{category}/{file_info['filename']}",
                'size': len(file_content),
                'mime_type': file_info['mime_type'],
                'thumbnails': {}
            }

            # 生成缩略图
            if generate_thumbnails:
                thumbnails = await self._generate_thumbnails(original_path, file_info)
                result['thumbnails'] = thumbnails

            logger.info(f"图片上传成功: {file_info['filename']}")
            return result

        except Exception as e:
            logger.error(f"图片上传失败: {e}")
            return {
                'success': False,
                'error': f"上传失败: {str(e)}"
            }

    async def upload_document(
        self, 
        file_content: bytes, 
        filename: str
    ) -> Dict[str, Any]:
        """
        上传文档
        
        Args:
            file_content: 文件内容
            filename: 原始文件名
            
        Returns:
            Dict包含上传结果信息
        """
        try:
            # 验证文件
            validation_result = await self._validate_document(file_content, filename)
            if not validation_result['valid']:
                return validation_result

            # 生成文件信息
            file_info = await self._generate_file_info(filename, "documents")
            
            # 保存文件
            file_path = await self._save_file(file_content, file_info['path'])
            
            result = {
                'success': True,
                'filename': file_info['filename'],
                'path': str(file_path),
                'url': f"/static/uploads/documents/{file_info['filename']}",
                'size': len(file_content),
                'mime_type': file_info['mime_type']
            }

            logger.info(f"文档上传成功: {file_info['filename']}")
            return result

        except Exception as e:
            logger.error(f"文档上传失败: {e}")
            return {
                'success': False,
                'error': f"上传失败: {str(e)}"
            }

    async def _validate_image(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """验证图片文件"""
        # 检查文件大小
        if len(file_content) > self.max_image_size:
            return {
                'valid': False,
                'error': f"图片文件过大，最大允许 {self.max_image_size // (1024*1024)}MB"
            }

        # 检查文件类型
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type not in self.allowed_image_types:
            return {
                'valid': False,
                'error': f"不支持的图片格式，支持: {', '.join(self.allowed_image_types)}"
            }

        # 验证图片内容
        try:
            image = Image.open(io.BytesIO(file_content))
            image.verify()
        except Exception:
            return {
                'valid': False,
                'error': "无效的图片文件"
            }

        return {'valid': True}

    async def _validate_document(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """验证文档文件"""
        # 检查文件大小
        if len(file_content) > self.max_file_size:
            return {
                'valid': False,
                'error': f"文件过大，最大允许 {self.max_file_size // (1024*1024)}MB"
            }

        # 检查文件类型
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type not in self.allowed_document_types:
            return {
                'valid': False,
                'error': f"不支持的文件格式，支持: {', '.join(self.allowed_document_types)}"
            }

        return {'valid': True}

    async def _generate_file_info(self, filename: str, category: str) -> Dict[str, Any]:
        """生成文件信息"""
        # 获取文件扩展名
        file_ext = Path(filename).suffix.lower()
        
        # 生成唯一文件名
        unique_id = str(uuid.uuid4())
        timestamp = datetime.now().strftime("%Y%m%d")
        new_filename = f"{timestamp}_{unique_id}{file_ext}"
        
        # 文件路径
        file_path = self.upload_dir / category / new_filename
        
        # MIME类型
        mime_type, _ = mimetypes.guess_type(filename)
        
        return {
            'filename': new_filename,
            'path': file_path,
            'mime_type': mime_type,
            'category': category
        }

    async def _save_file(self, file_content: bytes, file_path: Path) -> Path:
        """保存文件"""
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        return file_path

    async def _generate_thumbnails(self, original_path: Path, file_info: Dict) -> Dict[str, str]:
        """生成缩略图"""
        thumbnails = {}
        
        try:
            with Image.open(original_path) as image:
                # 转换为RGB模式（如果需要）
                if image.mode in ('RGBA', 'LA', 'P'):
                    image = image.convert('RGB')
                
                for size_name, (width, height) in self.thumbnail_sizes.items():
                    # 创建缩略图
                    thumbnail = ImageOps.fit(image, (width, height), Image.Resampling.LANCZOS)
                    
                    # 生成缩略图文件名
                    thumb_filename = f"{size_name}_{file_info['filename']}"
                    thumb_path = self.upload_dir / "thumbnails" / thumb_filename
                    
                    # 保存缩略图
                    thumbnail.save(thumb_path, 'JPEG', quality=85)
                    
                    thumbnails[size_name] = f"/static/uploads/thumbnails/{thumb_filename}"
                    
        except Exception as e:
            logger.error(f"生成缩略图失败: {e}")
            
        return thumbnails

    async def delete_file(self, file_path: str) -> bool:
        """删除文件"""
        try:
            # 删除原文件
            full_path = Path(file_path)
            if full_path.exists():
                full_path.unlink()
                
            # 删除相关缩略图
            if "uploads/images/" in file_path or "uploads/avatars/" in file_path or "uploads/covers/" in file_path:
                filename = full_path.name
                for size_name in self.thumbnail_sizes.keys():
                    thumb_path = self.upload_dir / "thumbnails" / f"{size_name}_{filename}"
                    if thumb_path.exists():
                        thumb_path.unlink()
                        
            return True
            
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return False

    async def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """获取文件信息"""
        try:
            full_path = Path(file_path)
            if not full_path.exists():
                return None
                
            stat = full_path.stat()
            mime_type, _ = mimetypes.guess_type(str(full_path))
            
            return {
                'filename': full_path.name,
                'size': stat.st_size,
                'mime_type': mime_type,
                'created_time': datetime.fromtimestamp(stat.st_ctime),
                'modified_time': datetime.fromtimestamp(stat.st_mtime)
            }
            
        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")
            return None

    async def calculate_file_hash(self, file_content: bytes) -> str:
        """计算文件哈希值"""
        return hashlib.md5(file_content).hexdigest()

    async def check_duplicate(self, file_content: bytes) -> Optional[str]:
        """检查重复文件"""
        file_hash = await self.calculate_file_hash(file_content)
        
        # 这里可以实现数据库查询，检查是否已存在相同哈希的文件
        # 暂时返回None，表示没有重复
        return None

    async def cleanup_old_files(self, days: int = 30) -> int:
        """清理旧文件"""
        try:
            from datetime import timedelta
            cutoff_time = datetime.now() - timedelta(days=days)
            deleted_count = 0
            
            for category_dir in self.upload_dir.iterdir():
                if category_dir.is_dir():
                    for file_path in category_dir.iterdir():
                        if file_path.is_file():
                            stat = file_path.stat()
                            if datetime.fromtimestamp(stat.st_mtime) < cutoff_time:
                                file_path.unlink()
                                deleted_count += 1
                                
            logger.info(f"清理了 {deleted_count} 个旧文件")
            return deleted_count
            
        except Exception as e:
            logger.error(f"清理旧文件失败: {e}")
            return 0

    def get_upload_stats(self) -> Dict[str, Any]:
        """获取上传统计信息"""
        try:
            stats = {
                'total_files': 0,
                'total_size': 0,
                'categories': {}
            }
            
            for category_dir in self.upload_dir.iterdir():
                if category_dir.is_dir():
                    category_stats = {
                        'count': 0,
                        'size': 0
                    }
                    
                    for file_path in category_dir.iterdir():
                        if file_path.is_file():
                            file_size = file_path.stat().st_size
                            category_stats['count'] += 1
                            category_stats['size'] += file_size
                            
                    stats['categories'][category_dir.name] = category_stats
                    stats['total_files'] += category_stats['count']
                    stats['total_size'] += category_stats['size']
                    
            return stats
            
        except Exception as e:
            logger.error(f"获取上传统计失败: {e}")
            return {}


# 全局文件上传管理器实例
file_upload_manager = FileUploadManager()
# app/utils/file_storage.py
# -*- coding: utf-8 -*-
"""
文件存储工具
提供文件上传、下载、管理功能
"""

import os
import uuid
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import aiofiles
from PIL import Image
from loguru import logger

try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False
    logger.warning("python-magic not installed, file type detection will be limited")

from app.config import settings
from app.core.exceptions import ValidationException


class FileStorageManager:
    """文件存储管理器"""

    def __init__(self):
        """初始化文件存储管理器"""
        self.upload_path = Path(settings.UPLOAD_PATH)
        self.max_upload_size = settings.MAX_UPLOAD_SIZE
        self.allowed_image_extensions = settings.ALLOWED_IMAGE_EXTENSIONS
        self.allowed_document_extensions = settings.ALLOWED_DOCUMENT_EXTENSIONS

        # 确保上传目录存在
        self.upload_path.mkdir(parents=True, exist_ok=True)

        # 创建子目录
        self._create_subdirectories()

    def _create_subdirectories(self) -> None:
        """创建子目录"""

        subdirs = [
            "images", "documents", "avatars",
            "covers", "temp", "exports"
        ]

        for subdir in subdirs:
            (self.upload_path / subdir).mkdir(exist_ok=True)

    def _get_file_extension(self, filename: str) -> str:
        """获取文件扩展名"""
        return Path(filename).suffix.lower()

    def _get_file_mime_type(self, file_path: Path) -> str:
        """获取文件MIME类型"""
        if not HAS_MAGIC:
            # 基于文件扩展名的简单MIME类型检测
            extension = file_path.suffix.lower()
            mime_types = {
                '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                '.png': 'image/png', '.gif': 'image/gif',
                '.webp': 'image/webp', '.bmp': 'image/bmp',
                '.txt': 'text/plain', '.pdf': 'application/pdf',
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            }
            return mime_types.get(extension, "application/octet-stream")
        
        try:
            return magic.from_file(str(file_path), mime=True)
        except Exception:
            return "application/octet-stream"

    def _generate_filename(self, original_filename: str) -> str:
        """生成唯一文件名"""

        extension = self._get_file_extension(original_filename)
        unique_id = str(uuid.uuid4())
        return f"{unique_id}{extension}"

    def _get_file_hash(self, file_path: Path) -> str:
        """计算文件哈希值"""

        hash_md5 = hashlib.md5()

        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)

        return hash_md5.hexdigest()

    async def save_file(
            self,
            file_content: bytes,
            filename: str,
            subdirectory: str = "temp",
            allowed_extensions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        保存文件

        Args:
            file_content: 文件内容
            filename: 原始文件名
            subdirectory: 子目录
            allowed_extensions: 允许的扩展名

        Returns:
            Dict[str, Any]: 文件信息

        Raises:
            ValidationException: 文件验证失败
        """

        try:
            # 检查文件大小
            if len(file_content) > self.max_upload_size:
                raise ValidationException(
                    f"文件大小超过限制 ({self.max_upload_size} bytes)"
                )

            # 检查文件扩展名
            extension = self._get_file_extension(filename)
            if allowed_extensions and extension not in allowed_extensions:
                raise ValidationException(f"不支持的文件类型: {extension}")

            # 生成文件路径
            new_filename = self._generate_filename(filename)
            file_dir = self.upload_path / subdirectory
            file_dir.mkdir(exist_ok=True)
            file_path = file_dir / new_filename

            # 保存文件
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)

            # 获取文件信息
            file_info = {
                "original_filename": filename,
                "filename": new_filename,
                "file_path": str(file_path),
                "relative_path": f"{subdirectory}/{new_filename}",
                "url": f"/static/uploads/{subdirectory}/{new_filename}",
                "size": len(file_content),
                "extension": extension,
                "mime_type": self._get_file_mime_type(file_path),
                "hash": self._get_file_hash(file_path)
            }

            logger.info(f"文件保存成功: {filename} -> {new_filename}")

            return file_info

        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"文件保存失败: {e}")
            raise ValidationException("文件保存失败")

    async def save_image(
            self,
            file_content: bytes,
            filename: str,
            subdirectory: str = "images",
            resize: Optional[Tuple[int, int]] = None,
            quality: int = 85
    ) -> Dict[str, Any]:
        """
        保存图片文件

        Args:
            file_content: 文件内容
            filename: 原始文件名
            subdirectory: 子目录
            resize: 调整大小 (width, height)
            quality: 图片质量

        Returns:
            Dict[str, Any]: 文件信息
        """

        try:
            # 验证图片格式
            extension = self._get_file_extension(filename)
            if extension not in self.allowed_image_extensions:
                raise ValidationException(f"不支持的图片格式: {extension}")

            # 保存原始文件
            file_info = await self.save_file(
                file_content=file_content,
                filename=filename,
                subdirectory=subdirectory,
                allowed_extensions=self.allowed_image_extensions
            )

            # 处理图片
            if resize or quality < 100:
                await self._process_image(
                    file_path=Path(file_info["file_path"]),
                    resize=resize,
                    quality=quality
                )

                # 重新计算文件信息
                processed_path = Path(file_info["file_path"])
                file_info["size"] = processed_path.stat().st_size
                file_info["hash"] = self._get_file_hash(processed_path)

            return file_info

        except ValidationException:
            raise
        except Exception as e:
            logger.error(f"图片保存失败: {e}")
            raise ValidationException("图片保存失败")

    async def _process_image(
            self,
            file_path: Path,
            resize: Optional[Tuple[int, int]] = None,
            quality: int = 85
    ) -> None:
        """
        处理图片（调整大小、压缩）

        Args:
            file_path: 图片路径
            resize: 调整大小
            quality: 图片质量
        """

        try:
            with Image.open(file_path) as img:
                # 转换为RGB模式（处理透明图片）
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')

                # 调整大小
                if resize:
                    img = img.resize(resize, Image.Resampling.LANCZOS)

                # 保存处理后的图片
                img.save(file_path, optimize=True, quality=quality)

        except Exception as e:
            logger.warning(f"图片处理失败: {e}")

    async def delete_file(self, file_path: str) -> bool:
        """
        删除文件

        Args:
            file_path: 文件路径

        Returns:
            bool: 删除成功
        """

        try:
            # 确保文件在上传目录内（安全检查）
            full_path = Path(file_path)
            if not str(full_path.resolve()).startswith(str(self.upload_path.resolve())):
                logger.warning(f"尝试删除上传目录外的文件: {file_path}")
                return False

            if full_path.exists():
                full_path.unlink()
                logger.info(f"文件删除成功: {file_path}")
                return True

            return False

        except Exception as e:
            logger.error(f"文件删除失败: {e}")
            return False

    async def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        获取文件信息

        Args:
            file_path: 文件路径

        Returns:
            Optional[Dict[str, Any]]: 文件信息
        """

        try:
            full_path = Path(file_path)

            if not full_path.exists():
                return None

            stat = full_path.stat()

            return {
                "filename": full_path.name,
                "file_path": str(full_path),
                "size": stat.st_size,
                "extension": full_path.suffix.lower(),
                "mime_type": self._get_file_mime_type(full_path),
                "created_at": stat.st_ctime,
                "modified_at": stat.st_mtime,
                "hash": self._get_file_hash(full_path)
            }

        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")
            return None

    async def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """
        清理临时文件

        Args:
            max_age_hours: 最大保留时间（小时）

        Returns:
            int: 清理的文件数量
        """

        try:
            temp_dir = self.upload_path / "temp"
            if not temp_dir.exists():
                return 0

            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600

            cleaned_count = 0

            for file_path in temp_dir.iterdir():
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime

                    if file_age > max_age_seconds:
                        file_path.unlink()
                        cleaned_count += 1

            logger.info(f"临时文件清理完成，清理了 {cleaned_count} 个文件")

            return cleaned_count

        except Exception as e:
            logger.error(f"临时文件清理失败: {e}")
            return 0


# 全局文件存储管理器实例
file_storage_manager = FileStorageManager()


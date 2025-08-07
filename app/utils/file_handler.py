# app/utils/file_handler.py
# -*- coding: utf-8 -*-
"""
文件处理工具模块
提供文件上传、下载、压缩、格式转换等功能
"""

import os
import shutil
import zipfile
import mimetypes
from typing import List, Optional, Dict, Any, Union, BinaryIO
from pathlib import Path
from datetime import datetime
from enum import Enum
from dataclasses import dataclass

import aiofiles
from PIL import Image
import magic


class FileType(Enum):
    """文件类型"""
    IMAGE = "image"
    DOCUMENT = "document"
    AUDIO = "audio"
    VIDEO = "video"
    ARCHIVE = "archive"
    TEXT = "text"
    OTHER = "other"


class ImageFormat(Enum):
    """图片格式"""
    JPEG = "JPEG"
    PNG = "PNG"
    WEBP = "WEBP"
    GIF = "GIF"
    BMP = "BMP"


@dataclass
class FileInfo:
    """文件信息"""
    filename: str
    size: int
    mime_type: str
    file_type: FileType
    extension: str
    created_at: datetime
    modified_at: datetime
    path: str
    url: Optional[str] = None
    thumbnail_url: Optional[str] = None


@dataclass
class UploadConfig:
    """上传配置"""
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: List[str] = None
    allowed_mime_types: List[str] = None
    upload_dir: str = "uploads"
    create_thumbnail: bool = True
    thumbnail_size: tuple = (200, 200)
    organize_by_date: bool = True


class FileValidator:
    """文件验证器"""
    
    def __init__(self, config: UploadConfig):
        self.config = config
    
    def validate_file(self, file_path: str, file_size: int) -> Dict[str, Any]:
        """验证文件"""
        errors = []
        
        # 检查文件大小
        if file_size > self.config.max_file_size:
            errors.append(f"文件大小超过限制 ({self.config.max_file_size} bytes)")
        
        # 检查文件扩展名
        if self.config.allowed_extensions:
            ext = Path(file_path).suffix.lower()
            if ext not in self.config.allowed_extensions:
                errors.append(f"不支持的文件扩展名: {ext}")
        
        # 检查MIME类型
        if self.config.allowed_mime_types:
            mime_type = self._get_mime_type(file_path)
            if mime_type not in self.config.allowed_mime_types:
                errors.append(f"不支持的文件类型: {mime_type}")
        
        # 检查文件内容（防止伪造扩展名）
        if not self._validate_file_content(file_path):
            errors.append("文件内容与扩展名不匹配")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _get_mime_type(self, file_path: str) -> str:
        """获取MIME类型"""
        try:
            return magic.from_file(file_path, mime=True)
        except:
            return mimetypes.guess_type(file_path)[0] or "application/octet-stream"
    
    def _validate_file_content(self, file_path: str) -> bool:
        """验证文件内容"""
        try:
            mime_type = self._get_mime_type(file_path)
            ext = Path(file_path).suffix.lower()
            
            # 图片文件验证
            if mime_type.startswith('image/'):
                try:
                    with Image.open(file_path) as img:
                        img.verify()
                    return True
                except:
                    return False
            
            # 其他文件类型的验证可以在这里添加
            return True
        except:
            return False


class FileManager:
    """文件管理器"""
    
    def __init__(self, config: UploadConfig):
        self.config = config
        self.validator = FileValidator(config)
        self.upload_dir = Path(config.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def get_file_type(self, mime_type: str) -> FileType:
        """根据MIME类型获取文件类型"""
        if mime_type.startswith('image/'):
            return FileType.IMAGE
        elif mime_type.startswith('audio/'):
            return FileType.AUDIO
        elif mime_type.startswith('video/'):
            return FileType.VIDEO
        elif mime_type.startswith('text/'):
            return FileType.TEXT
        elif mime_type in ['application/pdf', 'application/msword', 
                          'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            return FileType.DOCUMENT
        elif mime_type in ['application/zip', 'application/x-rar-compressed', 
                          'application/x-7z-compressed']:
            return FileType.ARCHIVE
        else:
            return FileType.OTHER
    
    def generate_filename(self, original_filename: str) -> str:
        """生成唯一文件名"""
        import uuid
        
        # 获取文件扩展名
        ext = Path(original_filename).suffix
        
        # 生成唯一文件名
        unique_name = f"{uuid.uuid4().hex}{ext}"
        
        return unique_name
    
    def get_upload_path(self, filename: str) -> Path:
        """获取上传路径"""
        if self.config.organize_by_date:
            # 按日期组织文件夹
            today = datetime.now()
            date_path = today.strftime("%Y/%m/%d")
            upload_path = self.upload_dir / date_path
        else:
            upload_path = self.upload_dir
        
        upload_path.mkdir(parents=True, exist_ok=True)
        return upload_path / filename
    
    async def save_file(self, file_data: BinaryIO, original_filename: str) -> FileInfo:
        """保存文件"""
        # 生成唯一文件名
        filename = self.generate_filename(original_filename)
        file_path = self.get_upload_path(filename)
        
        # 保存文件
        async with aiofiles.open(file_path, 'wb') as f:
            content = file_data.read()
            await f.write(content)
        
        # 验证文件
        validation_result = self.validator.validate_file(str(file_path), len(content))
        if not validation_result["valid"]:
            # 删除无效文件
            file_path.unlink(missing_ok=True)
            raise ValueError(f"文件验证失败: {', '.join(validation_result['errors'])}")
        
        # 获取文件信息
        file_info = self.get_file_info(str(file_path))
        
        # 创建缩略图（如果是图片）
        if file_info.file_type == FileType.IMAGE and self.config.create_thumbnail:
            thumbnail_path = await self.create_thumbnail(str(file_path))
            if thumbnail_path:
                file_info.thumbnail_url = str(thumbnail_path)
        
        return file_info
    
    def get_file_info(self, file_path: str) -> FileInfo:
        """获取文件信息"""
        path = Path(file_path)
        stat = path.stat()
        
        # 获取MIME类型
        mime_type = self.validator._get_mime_type(file_path)
        
        return FileInfo(
            filename=path.name,
            size=stat.st_size,
            mime_type=mime_type,
            file_type=self.get_file_type(mime_type),
            extension=path.suffix.lower(),
            created_at=datetime.fromtimestamp(stat.st_ctime),
            modified_at=datetime.fromtimestamp(stat.st_mtime),
            path=str(path),
            url=self.get_file_url(str(path))
        )
    
    def get_file_url(self, file_path: str) -> str:
        """获取文件URL"""
        # 这里应该根据实际的静态文件服务配置来生成URL
        relative_path = Path(file_path).relative_to(self.upload_dir)
        return f"/static/uploads/{relative_path}"
    
    async def create_thumbnail(self, image_path: str) -> Optional[str]:
        """创建缩略图"""
        try:
            path = Path(image_path)
            thumbnail_dir = path.parent / "thumbnails"
            thumbnail_dir.mkdir(exist_ok=True)
            
            thumbnail_path = thumbnail_dir / f"thumb_{path.name}"
            
            # 创建缩略图
            with Image.open(image_path) as img:
                # 转换为RGB模式（处理RGBA图片）
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # 创建缩略图
                img.thumbnail(self.config.thumbnail_size, Image.Resampling.LANCZOS)
                img.save(thumbnail_path, 'JPEG', quality=85)
            
            return str(thumbnail_path)
        except Exception as e:
            print(f"创建缩略图失败: {e}")
            return None
    
    def delete_file(self, file_path: str) -> bool:
        """删除文件"""
        try:
            path = Path(file_path)
            
            # 删除主文件
            if path.exists():
                path.unlink()
            
            # 删除缩略图
            thumbnail_path = path.parent / "thumbnails" / f"thumb_{path.name}"
            if thumbnail_path.exists():
                thumbnail_path.unlink()
            
            return True
        except Exception as e:
            print(f"删除文件失败: {e}")
            return False
    
    def move_file(self, src_path: str, dst_path: str) -> bool:
        """移动文件"""
        try:
            src = Path(src_path)
            dst = Path(dst_path)
            
            # 确保目标目录存在
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            # 移动文件
            shutil.move(str(src), str(dst))
            
            # 移动缩略图
            src_thumbnail = src.parent / "thumbnails" / f"thumb_{src.name}"
            if src_thumbnail.exists():
                dst_thumbnail = dst.parent / "thumbnails" / f"thumb_{dst.name}"
                dst_thumbnail.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src_thumbnail), str(dst_thumbnail))
            
            return True
        except Exception as e:
            print(f"移动文件失败: {e}")
            return False
    
    def copy_file(self, src_path: str, dst_path: str) -> bool:
        """复制文件"""
        try:
            src = Path(src_path)
            dst = Path(dst_path)
            
            # 确保目标目录存在
            dst.parent.mkdir(parents=True, exist_ok=True)
            
            # 复制文件
            shutil.copy2(str(src), str(dst))
            
            # 复制缩略图
            src_thumbnail = src.parent / "thumbnails" / f"thumb_{src.name}"
            if src_thumbnail.exists():
                dst_thumbnail = dst.parent / "thumbnails" / f"thumb_{dst.name}"
                dst_thumbnail.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(str(src_thumbnail), str(dst_thumbnail))
            
            return True
        except Exception as e:
            print(f"复制文件失败: {e}")
            return False


class ImageProcessor:
    """图片处理器"""
    
    @staticmethod
    def resize_image(input_path: str, output_path: str, size: tuple, 
                    quality: int = 85) -> bool:
        """调整图片大小"""
        try:
            with Image.open(input_path) as img:
                # 转换为RGB模式
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # 调整大小
                img = img.resize(size, Image.Resampling.LANCZOS)
                
                # 保存
                img.save(output_path, 'JPEG', quality=quality)
            
            return True
        except Exception as e:
            print(f"调整图片大小失败: {e}")
            return False
    
    @staticmethod
    def crop_image(input_path: str, output_path: str, box: tuple) -> bool:
        """裁剪图片"""
        try:
            with Image.open(input_path) as img:
                # 裁剪
                cropped = img.crop(box)
                
                # 保存
                cropped.save(output_path)
            
            return True
        except Exception as e:
            print(f"裁剪图片失败: {e}")
            return False
    
    @staticmethod
    def convert_format(input_path: str, output_path: str, 
                      format: ImageFormat, quality: int = 85) -> bool:
        """转换图片格式"""
        try:
            with Image.open(input_path) as img:
                # 转换格式
                if format == ImageFormat.JPEG and img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # 保存
                save_kwargs = {}
                if format == ImageFormat.JPEG:
                    save_kwargs['quality'] = quality
                elif format == ImageFormat.PNG:
                    save_kwargs['optimize'] = True
                elif format == ImageFormat.WEBP:
                    save_kwargs['quality'] = quality
                    save_kwargs['method'] = 6
                
                img.save(output_path, format.value, **save_kwargs)
            
            return True
        except Exception as e:
            print(f"转换图片格式失败: {e}")
            return False
    
    @staticmethod
    def add_watermark(input_path: str, output_path: str, watermark_path: str,
                     position: str = "bottom-right", opacity: float = 0.5) -> bool:
        """添加水印"""
        try:
            with Image.open(input_path) as base_img:
                with Image.open(watermark_path) as watermark:
                    # 调整水印透明度
                    if watermark.mode != 'RGBA':
                        watermark = watermark.convert('RGBA')
                    
                    # 创建透明度蒙版
                    alpha = watermark.split()[-1]
                    alpha = alpha.point(lambda p: int(p * opacity))
                    watermark.putalpha(alpha)
                    
                    # 计算水印位置
                    base_width, base_height = base_img.size
                    watermark_width, watermark_height = watermark.size
                    
                    if position == "top-left":
                        pos = (10, 10)
                    elif position == "top-right":
                        pos = (base_width - watermark_width - 10, 10)
                    elif position == "bottom-left":
                        pos = (10, base_height - watermark_height - 10)
                    elif position == "bottom-right":
                        pos = (base_width - watermark_width - 10, 
                              base_height - watermark_height - 10)
                    else:  # center
                        pos = ((base_width - watermark_width) // 2,
                              (base_height - watermark_height) // 2)
                    
                    # 添加水印
                    if base_img.mode != 'RGBA':
                        base_img = base_img.convert('RGBA')
                    
                    base_img.paste(watermark, pos, watermark)
                    
                    # 保存
                    if output_path.lower().endswith('.jpg') or output_path.lower().endswith('.jpeg'):
                        base_img = base_img.convert('RGB')
                    
                    base_img.save(output_path)
            
            return True
        except Exception as e:
            print(f"添加水印失败: {e}")
            return False


class ArchiveManager:
    """压缩文件管理器"""
    
    @staticmethod
    def create_zip(file_paths: List[str], output_path: str) -> bool:
        """创建ZIP压缩文件"""
        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in file_paths:
                    path = Path(file_path)
                    if path.exists():
                        zipf.write(file_path, path.name)
            return True
        except Exception as e:
            print(f"创建ZIP文件失败: {e}")
            return False
    
    @staticmethod
    def extract_zip(zip_path: str, extract_dir: str) -> bool:
        """解压ZIP文件"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(extract_dir)
            return True
        except Exception as e:
            print(f"解压ZIP文件失败: {e}")
            return False
    
    @staticmethod
    def list_zip_contents(zip_path: str) -> List[str]:
        """列出ZIP文件内容"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                return zipf.namelist()
        except Exception as e:
            print(f"读取ZIP文件内容失败: {e}")
            return []


# 默认配置
default_upload_config = UploadConfig(
    max_file_size=10 * 1024 * 1024,  # 10MB
    allowed_extensions=['.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf', '.txt', '.doc', '.docx'],
    upload_dir="uploads",
    create_thumbnail=True,
    thumbnail_size=(200, 200),
    organize_by_date=True
)

# 全局文件管理器实例
file_manager = FileManager(default_upload_config)


# 便捷函数
async def save_uploaded_file(file_data: BinaryIO, filename: str) -> FileInfo:
    """保存上传的文件"""
    return await file_manager.save_file(file_data, filename)


def delete_uploaded_file(file_path: str) -> bool:
    """删除上传的文件"""
    return file_manager.delete_file(file_path)


def get_file_info(file_path: str) -> FileInfo:
    """获取文件信息"""
    return file_manager.get_file_info(file_path)
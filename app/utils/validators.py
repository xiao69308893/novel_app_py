# app/utils/validators.py
# -*- coding: utf-8 -*-
"""
数据验证工具模块
提供各种数据验证功能
"""

import re
import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from email_validator import validate_email, EmailNotValidError
from pydantic import BaseModel, ValidationError


class ValidationResult:
    """验证结果类"""
    
    def __init__(self, is_valid: bool = True, errors: Optional[List[str]] = None):
        self.is_valid = is_valid
        self.errors = errors or []
    
    def add_error(self, error: str):
        """添加错误信息"""
        self.is_valid = False
        self.errors.append(error)
    
    def __bool__(self):
        return self.is_valid


class BaseValidator:
    """基础验证器"""
    
    @staticmethod
    def is_empty(value: Any) -> bool:
        """检查值是否为空"""
        if value is None:
            return True
        if isinstance(value, str) and not value.strip():
            return True
        if isinstance(value, (list, dict, tuple)) and len(value) == 0:
            return True
        return False
    
    @staticmethod
    def is_length_valid(value: str, min_length: int = 0, max_length: int = None) -> bool:
        """检查字符串长度"""
        if not isinstance(value, str):
            return False
        length = len(value)
        if length < min_length:
            return False
        if max_length is not None and length > max_length:
            return False
        return True
    
    @staticmethod
    def is_in_range(value: Union[int, float], min_value: Union[int, float] = None, 
                    max_value: Union[int, float] = None) -> bool:
        """检查数值范围"""
        if not isinstance(value, (int, float)):
            return False
        if min_value is not None and value < min_value:
            return False
        if max_value is not None and value > max_value:
            return False
        return True


class StringValidator(BaseValidator):
    """字符串验证器"""
    
    # 常用正则表达式
    PATTERNS = {
        'username': r'^[a-zA-Z0-9_]{3,20}$',
        'password': r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d@$!%*?&]{8,}$',
        'phone': r'^1[3-9]\d{9}$',
        'id_card': r'^\d{17}[\dXx]$',
        'url': r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$',
        'ipv4': r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$',
        'chinese': r'^[\u4e00-\u9fa5]+$',
        'alphanumeric': r'^[a-zA-Z0-9]+$',
        'slug': r'^[a-z0-9]+(?:-[a-z0-9]+)*$'
    }
    
    @classmethod
    def validate_pattern(cls, value: str, pattern: str) -> bool:
        """验证字符串模式"""
        if not isinstance(value, str):
            return False
        return bool(re.match(pattern, value))
    
    @classmethod
    def validate_username(cls, username: str) -> ValidationResult:
        """验证用户名"""
        result = ValidationResult()
        
        if cls.is_empty(username):
            result.add_error("用户名不能为空")
            return result
        
        if not cls.is_length_valid(username, 3, 20):
            result.add_error("用户名长度必须在3-20个字符之间")
        
        if not cls.validate_pattern(username, cls.PATTERNS['username']):
            result.add_error("用户名只能包含字母、数字和下划线")
        
        return result
    
    @classmethod
    def validate_password(cls, password: str) -> ValidationResult:
        """验证密码强度"""
        result = ValidationResult()
        
        if cls.is_empty(password):
            result.add_error("密码不能为空")
            return result
        
        if not cls.is_length_valid(password, 8, 128):
            result.add_error("密码长度必须在8-128个字符之间")
        
        if not re.search(r'[a-z]', password):
            result.add_error("密码必须包含小写字母")
        
        if not re.search(r'[A-Z]', password):
            result.add_error("密码必须包含大写字母")
        
        if not re.search(r'\d', password):
            result.add_error("密码必须包含数字")
        
        return result
    
    @classmethod
    def validate_email(cls, email: str) -> ValidationResult:
        """验证邮箱地址"""
        result = ValidationResult()
        
        if cls.is_empty(email):
            result.add_error("邮箱地址不能为空")
            return result
        
        try:
            validate_email(email)
        except EmailNotValidError as e:
            result.add_error(f"邮箱地址格式无效: {str(e)}")
        
        return result
    
    @classmethod
    def validate_phone(cls, phone: str) -> ValidationResult:
        """验证手机号码"""
        result = ValidationResult()
        
        if cls.is_empty(phone):
            result.add_error("手机号码不能为空")
            return result
        
        if not cls.validate_pattern(phone, cls.PATTERNS['phone']):
            result.add_error("手机号码格式无效")
        
        return result
    
    @classmethod
    def validate_id_card(cls, id_card: str) -> ValidationResult:
        """验证身份证号码"""
        result = ValidationResult()
        
        if cls.is_empty(id_card):
            result.add_error("身份证号码不能为空")
            return result
        
        if not cls.validate_pattern(id_card, cls.PATTERNS['id_card']):
            result.add_error("身份证号码格式无效")
        
        return result
    
    @classmethod
    def validate_url(cls, url: str) -> ValidationResult:
        """验证URL地址"""
        result = ValidationResult()
        
        if cls.is_empty(url):
            result.add_error("URL地址不能为空")
            return result
        
        if not cls.validate_pattern(url, cls.PATTERNS['url']):
            result.add_error("URL地址格式无效")
        
        return result


class NumberValidator(BaseValidator):
    """数字验证器"""
    
    @classmethod
    def validate_integer(cls, value: Any, min_value: int = None, max_value: int = None) -> ValidationResult:
        """验证整数"""
        result = ValidationResult()
        
        if value is None:
            result.add_error("值不能为空")
            return result
        
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            result.add_error("值必须是整数")
            return result
        
        if not cls.is_in_range(int_value, min_value, max_value):
            if min_value is not None and max_value is not None:
                result.add_error(f"值必须在{min_value}到{max_value}之间")
            elif min_value is not None:
                result.add_error(f"值必须大于等于{min_value}")
            elif max_value is not None:
                result.add_error(f"值必须小于等于{max_value}")
        
        return result
    
    @classmethod
    def validate_float(cls, value: Any, min_value: float = None, max_value: float = None) -> ValidationResult:
        """验证浮点数"""
        result = ValidationResult()
        
        if value is None:
            result.add_error("值不能为空")
            return result
        
        try:
            float_value = float(value)
        except (ValueError, TypeError):
            result.add_error("值必须是数字")
            return result
        
        if not cls.is_in_range(float_value, min_value, max_value):
            if min_value is not None and max_value is not None:
                result.add_error(f"值必须在{min_value}到{max_value}之间")
            elif min_value is not None:
                result.add_error(f"值必须大于等于{min_value}")
            elif max_value is not None:
                result.add_error(f"值必须小于等于{max_value}")
        
        return result
    
    @classmethod
    def validate_decimal(cls, value: Any, max_digits: int = None, decimal_places: int = None) -> ValidationResult:
        """验证小数"""
        result = ValidationResult()
        
        if value is None:
            result.add_error("值不能为空")
            return result
        
        try:
            decimal_value = Decimal(str(value))
        except (InvalidOperation, ValueError):
            result.add_error("值必须是有效的小数")
            return result
        
        if max_digits is not None:
            total_digits = len(str(decimal_value).replace('.', '').replace('-', ''))
            if total_digits > max_digits:
                result.add_error(f"总位数不能超过{max_digits}位")
        
        if decimal_places is not None:
            _, _, exponent = decimal_value.as_tuple()
            if abs(exponent) > decimal_places:
                result.add_error(f"小数位数不能超过{decimal_places}位")
        
        return result


class DateTimeValidator(BaseValidator):
    """日期时间验证器"""
    
    @classmethod
    def validate_date(cls, value: Any, date_format: str = "%Y-%m-%d") -> ValidationResult:
        """验证日期"""
        result = ValidationResult()
        
        if value is None:
            result.add_error("日期不能为空")
            return result
        
        if isinstance(value, date):
            return result
        
        if isinstance(value, str):
            try:
                datetime.strptime(value, date_format)
            except ValueError:
                result.add_error(f"日期格式无效，应为{date_format}")
        else:
            result.add_error("日期格式无效")
        
        return result
    
    @classmethod
    def validate_datetime(cls, value: Any, datetime_format: str = "%Y-%m-%d %H:%M:%S") -> ValidationResult:
        """验证日期时间"""
        result = ValidationResult()
        
        if value is None:
            result.add_error("日期时间不能为空")
            return result
        
        if isinstance(value, datetime):
            return result
        
        if isinstance(value, str):
            try:
                datetime.strptime(value, datetime_format)
            except ValueError:
                result.add_error(f"日期时间格式无效，应为{datetime_format}")
        else:
            result.add_error("日期时间格式无效")
        
        return result
    
    @classmethod
    def validate_date_range(cls, start_date: Any, end_date: Any) -> ValidationResult:
        """验证日期范围"""
        result = ValidationResult()
        
        start_result = cls.validate_date(start_date)
        end_result = cls.validate_date(end_date)
        
        if not start_result.is_valid:
            result.errors.extend([f"开始日期: {error}" for error in start_result.errors])
        
        if not end_result.is_valid:
            result.errors.extend([f"结束日期: {error}" for error in end_result.errors])
        
        if start_result.is_valid and end_result.is_valid:
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            
            if start_date > end_date:
                result.add_error("开始日期不能晚于结束日期")
        
        return result


class FileValidator(BaseValidator):
    """文件验证器"""
    
    @classmethod
    def validate_file_size(cls, file_size: int, max_size: int) -> ValidationResult:
        """验证文件大小"""
        result = ValidationResult()
        
        if file_size <= 0:
            result.add_error("文件大小无效")
        elif file_size > max_size:
            result.add_error(f"文件大小不能超过{max_size / 1024 / 1024:.1f}MB")
        
        return result
    
    @classmethod
    def validate_file_extension(cls, filename: str, allowed_extensions: List[str]) -> ValidationResult:
        """验证文件扩展名"""
        result = ValidationResult()
        
        if cls.is_empty(filename):
            result.add_error("文件名不能为空")
            return result
        
        extension = filename.lower().split('.')[-1] if '.' in filename else ''
        if extension not in [ext.lower() for ext in allowed_extensions]:
            result.add_error(f"文件类型不支持，允许的类型: {', '.join(allowed_extensions)}")
        
        return result
    
    @classmethod
    def validate_image_dimensions(cls, width: int, height: int, 
                                 max_width: int = None, max_height: int = None,
                                 min_width: int = None, min_height: int = None) -> ValidationResult:
        """验证图片尺寸"""
        result = ValidationResult()
        
        if max_width and width > max_width:
            result.add_error(f"图片宽度不能超过{max_width}像素")
        
        if max_height and height > max_height:
            result.add_error(f"图片高度不能超过{max_height}像素")
        
        if min_width and width < min_width:
            result.add_error(f"图片宽度不能小于{min_width}像素")
        
        if min_height and height < min_height:
            result.add_error(f"图片高度不能小于{min_height}像素")
        
        return result


class JSONValidator(BaseValidator):
    """JSON验证器"""
    
    @classmethod
    def validate_json(cls, value: str) -> ValidationResult:
        """验证JSON格式"""
        result = ValidationResult()
        
        if cls.is_empty(value):
            result.add_error("JSON数据不能为空")
            return result
        
        try:
            json.loads(value)
        except json.JSONDecodeError as e:
            result.add_error(f"JSON格式无效: {str(e)}")
        
        return result
    
    @classmethod
    def validate_json_schema(cls, value: str, schema: Dict[str, Any]) -> ValidationResult:
        """验证JSON Schema"""
        result = ValidationResult()
        
        json_result = cls.validate_json(value)
        if not json_result.is_valid:
            return json_result
        
        try:
            import jsonschema
            data = json.loads(value)
            jsonschema.validate(data, schema)
        except ImportError:
            result.add_error("jsonschema库未安装，无法验证Schema")
        except jsonschema.ValidationError as e:
            result.add_error(f"JSON Schema验证失败: {str(e)}")
        except Exception as e:
            result.add_error(f"Schema验证错误: {str(e)}")
        
        return result


class ModelValidator(BaseValidator):
    """模型验证器"""
    
    @classmethod
    def validate_pydantic_model(cls, data: Dict[str, Any], model_class: BaseModel) -> ValidationResult:
        """验证Pydantic模型"""
        result = ValidationResult()
        
        try:
            model_class(**data)
        except ValidationError as e:
            for error in e.errors():
                field = '.'.join(str(loc) for loc in error['loc'])
                message = error['msg']
                result.add_error(f"{field}: {message}")
        except Exception as e:
            result.add_error(f"模型验证错误: {str(e)}")
        
        return result


class CompositeValidator:
    """复合验证器"""
    
    def __init__(self):
        self.validators = []
    
    def add_validator(self, validator_func, *args, **kwargs):
        """添加验证器"""
        self.validators.append((validator_func, args, kwargs))
        return self
    
    def validate(self, value: Any) -> ValidationResult:
        """执行所有验证"""
        result = ValidationResult()
        
        for validator_func, args, kwargs in self.validators:
            validator_result = validator_func(value, *args, **kwargs)
            if not validator_result.is_valid:
                result.errors.extend(validator_result.errors)
                result.is_valid = False
        
        return result


# 便捷函数
def validate_username(username: str) -> ValidationResult:
    """验证用户名"""
    return StringValidator.validate_username(username)


def validate_password(password: str) -> ValidationResult:
    """验证密码"""
    return StringValidator.validate_password(password)


def validate_email(email: str) -> ValidationResult:
    """验证邮箱"""
    return StringValidator.validate_email(email)


def validate_phone(phone: str) -> ValidationResult:
    """验证手机号"""
    return StringValidator.validate_phone(phone)


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> ValidationResult:
    """验证必填字段"""
    result = ValidationResult()
    
    for field in required_fields:
        if field not in data or BaseValidator.is_empty(data[field]):
            result.add_error(f"字段 {field} 是必填的")
    
    return result


def validate_choice(value: Any, choices: List[Any], field_name: str = "值") -> ValidationResult:
    """验证选择项"""
    result = ValidationResult()
    
    if value not in choices:
        result.add_error(f"{field_name}必须是以下选项之一: {', '.join(map(str, choices))}")
    
    return result


# 全局验证器实例
string_validator = StringValidator()
number_validator = NumberValidator()
datetime_validator = DateTimeValidator()
file_validator = FileValidator()
json_validator = JSONValidator()
model_validator = ModelValidator()
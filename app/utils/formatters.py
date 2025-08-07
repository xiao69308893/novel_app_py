# app/utils/formatters.py
# -*- coding: utf-8 -*-
"""
数据格式化工具模块
提供各种数据格式化功能
"""

import re
import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date, timedelta
from decimal import Decimal
from urllib.parse import quote, unquote


class TextFormatter:
    """文本格式化器"""
    
    @staticmethod
    def truncate(text: str, length: int, suffix: str = "...") -> str:
        """截断文本"""
        if not text or len(text) <= length:
            return text
        return text[:length - len(suffix)] + suffix
    
    @staticmethod
    def capitalize_words(text: str) -> str:
        """首字母大写"""
        return ' '.join(word.capitalize() for word in text.split())
    
    @staticmethod
    def snake_to_camel(snake_str: str) -> str:
        """蛇形命名转驼峰命名"""
        components = snake_str.split('_')
        return components[0] + ''.join(x.capitalize() for x in components[1:])
    
    @staticmethod
    def camel_to_snake(camel_str: str) -> str:
        """驼峰命名转蛇形命名"""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_str)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    
    @staticmethod
    def remove_html_tags(text: str) -> str:
        """移除HTML标签"""
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text)
    
    @staticmethod
    def escape_html(text: str) -> str:
        """转义HTML特殊字符"""
        html_escape_table = {
            "&": "&amp;",
            '"': "&quot;",
            "'": "&#x27;",
            ">": "&gt;",
            "<": "&lt;",
        }
        return "".join(html_escape_table.get(c, c) for c in text)
    
    @staticmethod
    def unescape_html(text: str) -> str:
        """反转义HTML特殊字符"""
        html_unescape_table = {
            "&amp;": "&",
            "&quot;": '"',
            "&#x27;": "'",
            "&gt;": ">",
            "&lt;": "<",
        }
        for escaped, unescaped in html_unescape_table.items():
            text = text.replace(escaped, unescaped)
        return text
    
    @staticmethod
    def clean_whitespace(text: str) -> str:
        """清理多余空白字符"""
        return re.sub(r'\s+', ' ', text.strip())
    
    @staticmethod
    def extract_numbers(text: str) -> List[str]:
        """提取文本中的数字"""
        return re.findall(r'\d+\.?\d*', text)
    
    @staticmethod
    def mask_sensitive_info(text: str, mask_char: str = "*") -> str:
        """掩码敏感信息"""
        # 掩码手机号
        text = re.sub(r'(\d{3})\d{4}(\d{4})', r'\1****\2', text)
        # 掩码邮箱
        text = re.sub(r'(\w{1,3})\w*@', r'\1***@', text)
        # 掩码身份证
        text = re.sub(r'(\d{6})\d{8}(\d{4})', r'\1********\2', text)
        return text
    
    @staticmethod
    def generate_slug(text: str) -> str:
        """生成URL友好的slug"""
        # 转换为小写
        text = text.lower()
        # 移除特殊字符，保留字母数字和空格
        text = re.sub(r'[^a-z0-9\s-]', '', text)
        # 将空格和多个连字符替换为单个连字符
        text = re.sub(r'[\s-]+', '-', text)
        # 移除首尾连字符
        return text.strip('-')


class NumberFormatter:
    """数字格式化器"""
    
    @staticmethod
    def format_currency(amount: Union[int, float, Decimal], currency: str = "¥", 
                       decimal_places: int = 2) -> str:
        """格式化货币"""
        if isinstance(amount, Decimal):
            amount = float(amount)
        return f"{currency}{amount:,.{decimal_places}f}"
    
    @staticmethod
    def format_percentage(value: Union[int, float], decimal_places: int = 2) -> str:
        """格式化百分比"""
        return f"{value:.{decimal_places}f}%"
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """格式化文件大小"""
        if size_bytes == 0:
            return "0B"
        
        size_names = ["B", "KB", "MB", "GB", "TB", "PB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f}{size_names[i]}"
    
    @staticmethod
    def format_number_with_units(number: Union[int, float]) -> str:
        """格式化数字带单位（万、亿等）"""
        if number < 10000:
            return str(int(number))
        elif number < 100000000:
            return f"{number / 10000:.1f}万"
        else:
            return f"{number / 100000000:.1f}亿"
    
    @staticmethod
    def format_ordinal(number: int) -> str:
        """格式化序数词"""
        if 10 <= number % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(number % 10, 'th')
        return f"{number}{suffix}"
    
    @staticmethod
    def format_scientific(number: Union[int, float], precision: int = 2) -> str:
        """格式化科学计数法"""
        return f"{number:.{precision}e}"
    
    @staticmethod
    def format_roman_numeral(number: int) -> str:
        """格式化罗马数字"""
        if not 1 <= number <= 3999:
            raise ValueError("Roman numerals are only defined for 1-3999")
        
        values = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
        symbols = ["M", "CM", "D", "CD", "C", "XC", "L", "XL", "X", "IX", "V", "IV", "I"]
        
        result = ""
        for i, value in enumerate(values):
            count = number // value
            result += symbols[i] * count
            number -= value * count
        
        return result


class DateTimeFormatter:
    """日期时间格式化器"""
    
    @staticmethod
    def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """格式化日期时间"""
        return dt.strftime(format_str)
    
    @staticmethod
    def format_date(dt: Union[datetime, date], format_str: str = "%Y-%m-%d") -> str:
        """格式化日期"""
        if isinstance(dt, datetime):
            dt = dt.date()
        return dt.strftime(format_str)
    
    @staticmethod
    def format_time(dt: datetime, format_str: str = "%H:%M:%S") -> str:
        """格式化时间"""
        return dt.strftime(format_str)
    
    @staticmethod
    def format_relative_time(dt: datetime, now: Optional[datetime] = None) -> str:
        """格式化相对时间"""
        if now is None:
            now = datetime.now()
        
        diff = now - dt
        
        if diff.days > 0:
            if diff.days == 1:
                return "1天前"
            elif diff.days < 30:
                return f"{diff.days}天前"
            elif diff.days < 365:
                months = diff.days // 30
                return f"{months}个月前"
            else:
                years = diff.days // 365
                return f"{years}年前"
        
        seconds = diff.seconds
        if seconds < 60:
            return "刚刚"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes}分钟前"
        else:
            hours = seconds // 3600
            return f"{hours}小时前"
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        """格式化时长"""
        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            if remaining_seconds == 0:
                return f"{minutes}分钟"
            return f"{minutes}分{remaining_seconds}秒"
        else:
            hours = seconds // 3600
            remaining_minutes = (seconds % 3600) // 60
            if remaining_minutes == 0:
                return f"{hours}小时"
            return f"{hours}小时{remaining_minutes}分钟"
    
    @staticmethod
    def format_age(birth_date: date, reference_date: Optional[date] = None) -> str:
        """格式化年龄"""
        if reference_date is None:
            reference_date = date.today()
        
        age = reference_date.year - birth_date.year
        if reference_date.month < birth_date.month or \
           (reference_date.month == birth_date.month and reference_date.day < birth_date.day):
            age -= 1
        
        return f"{age}岁"
    
    @staticmethod
    def format_chinese_date(dt: Union[datetime, date]) -> str:
        """格式化中文日期"""
        if isinstance(dt, datetime):
            dt = dt.date()
        
        year = dt.year
        month = dt.month
        day = dt.day
        
        return f"{year}年{month}月{day}日"
    
    @staticmethod
    def format_weekday(dt: Union[datetime, date], lang: str = "zh") -> str:
        """格式化星期"""
        if isinstance(dt, datetime):
            dt = dt.date()
        
        weekday = dt.weekday()
        
        if lang == "zh":
            weekdays = ["一", "二", "三", "四", "五", "六", "日"]
            return f"星期{weekdays[weekday]}"
        else:
            weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            return weekdays[weekday]


class URLFormatter:
    """URL格式化器"""
    
    @staticmethod
    def encode_url(url: str) -> str:
        """URL编码"""
        return quote(url, safe=':/?#[]@!$&\'()*+,;=')
    
    @staticmethod
    def decode_url(url: str) -> str:
        """URL解码"""
        return unquote(url)
    
    @staticmethod
    def build_query_string(params: Dict[str, Any]) -> str:
        """构建查询字符串"""
        query_parts = []
        for key, value in params.items():
            if value is not None:
                if isinstance(value, list):
                    for item in value:
                        query_parts.append(f"{quote(str(key))}={quote(str(item))}")
                else:
                    query_parts.append(f"{quote(str(key))}={quote(str(value))}")
        return "&".join(query_parts)
    
    @staticmethod
    def parse_query_string(query_string: str) -> Dict[str, List[str]]:
        """解析查询字符串"""
        params = {}
        if not query_string:
            return params
        
        for part in query_string.split('&'):
            if '=' in part:
                key, value = part.split('=', 1)
                key = unquote(key)
                value = unquote(value)
                
                if key in params:
                    params[key].append(value)
                else:
                    params[key] = [value]
        
        return params
    
    @staticmethod
    def normalize_url(url: str) -> str:
        """标准化URL"""
        # 移除末尾斜杠
        url = url.rstrip('/')
        # 转换为小写（除了查询参数）
        if '?' in url:
            base, query = url.split('?', 1)
            url = base.lower() + '?' + query
        else:
            url = url.lower()
        return url


class JSONFormatter:
    """JSON格式化器"""
    
    @staticmethod
    def format_json(data: Any, indent: int = 2, ensure_ascii: bool = False) -> str:
        """格式化JSON"""
        return json.dumps(data, indent=indent, ensure_ascii=ensure_ascii, 
                         separators=(',', ': '), default=str)
    
    @staticmethod
    def minify_json(data: Any) -> str:
        """压缩JSON"""
        return json.dumps(data, separators=(',', ':'), ensure_ascii=False, default=str)
    
    @staticmethod
    def format_json_for_display(data: Any, max_length: int = 100) -> str:
        """格式化JSON用于显示"""
        json_str = json.dumps(data, ensure_ascii=False, default=str)
        if len(json_str) <= max_length:
            return json_str
        return json_str[:max_length - 3] + "..."


class ListFormatter:
    """列表格式化器"""
    
    @staticmethod
    def format_list(items: List[Any], separator: str = ", ", 
                   last_separator: str = " 和 ") -> str:
        """格式化列表为字符串"""
        if not items:
            return ""
        if len(items) == 1:
            return str(items[0])
        if len(items) == 2:
            return f"{items[0]}{last_separator}{items[1]}"
        
        return separator.join(str(item) for item in items[:-1]) + last_separator + str(items[-1])
    
    @staticmethod
    def format_numbered_list(items: List[Any], start: int = 1) -> str:
        """格式化编号列表"""
        return "\n".join(f"{i + start}. {item}" for i, item in enumerate(items))
    
    @staticmethod
    def format_bulleted_list(items: List[Any], bullet: str = "•") -> str:
        """格式化项目符号列表"""
        return "\n".join(f"{bullet} {item}" for item in items)
    
    @staticmethod
    def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
        """将列表分块"""
        return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


class TableFormatter:
    """表格格式化器"""
    
    @staticmethod
    def format_table(data: List[Dict[str, Any]], headers: Optional[List[str]] = None) -> str:
        """格式化表格"""
        if not data:
            return ""
        
        if headers is None:
            headers = list(data[0].keys())
        
        # 计算列宽
        col_widths = {}
        for header in headers:
            col_widths[header] = len(str(header))
            for row in data:
                col_widths[header] = max(col_widths[header], len(str(row.get(header, ""))))
        
        # 构建表格
        lines = []
        
        # 表头
        header_line = " | ".join(str(header).ljust(col_widths[header]) for header in headers)
        lines.append(header_line)
        
        # 分隔线
        separator_line = " | ".join("-" * col_widths[header] for header in headers)
        lines.append(separator_line)
        
        # 数据行
        for row in data:
            data_line = " | ".join(str(row.get(header, "")).ljust(col_widths[header]) for header in headers)
            lines.append(data_line)
        
        return "\n".join(lines)


# 便捷函数
def truncate_text(text: str, length: int, suffix: str = "...") -> str:
    """截断文本"""
    return TextFormatter.truncate(text, length, suffix)


def format_currency(amount: Union[int, float, Decimal], currency: str = "¥") -> str:
    """格式化货币"""
    return NumberFormatter.format_currency(amount, currency)


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    return NumberFormatter.format_file_size(size_bytes)


def format_relative_time(dt: datetime) -> str:
    """格式化相对时间"""
    return DateTimeFormatter.format_relative_time(dt)


def format_duration(seconds: int) -> str:
    """格式化时长"""
    return DateTimeFormatter.format_duration(seconds)


def format_json(data: Any, indent: int = 2) -> str:
    """格式化JSON"""
    return JSONFormatter.format_json(data, indent)


def generate_slug(text: str) -> str:
    """生成URL友好的slug"""
    return TextFormatter.generate_slug(text)


# 全局格式化器实例
text_formatter = TextFormatter()
number_formatter = NumberFormatter()
datetime_formatter = DateTimeFormatter()
url_formatter = URLFormatter()
json_formatter = JSONFormatter()
list_formatter = ListFormatter()
table_formatter = TableFormatter()
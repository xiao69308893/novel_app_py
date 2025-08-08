#!/usr/bin/env python3
"""
快速修复Pydantic v2兼容性问题
专门针对当前项目的错误
"""

import os
import re


def quick_fix_analytics():
    """快速修复analytics.py文件"""
    file_path = "app/schemas/analytics.py"

    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False

    print(f"🔧 修复文件: {file_path}")

    try:
        # 读取文件
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 备份
        with open(f"{file_path}.backup", 'w', encoding='utf-8') as f:
            f.write(content)
        print("  ✓ 已创建备份")

        # 1. 确保导入ConfigDict
        if 'ConfigDict' not in content:
            content = re.sub(
                r'from pydantic import ([^\\n]+)',
                r'from pydantic import \\1, ConfigDict',
                content
            )
            print("  ✓ 添加ConfigDict导入")

        # 2. 修复所有Config类为model_config
        content = re.sub(
            r'class Config:\\s*\\n\\s*schema_extra = ({[^}]*})',
            r'model_config = ConfigDict(json_schema_extra=\\1)',
            content,
            flags=re.DOTALL
        )

        # 3. 特别修复ReadingTrendResponse类
        reading_trend_fix = '''class ReadingTrendResponse(BaseModel):
    """阅读趋势响应"""
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "date": "2024-01-01",
                "active_readers": 500,
                "total_reading_time": 15000,
                "reading_sessions": 800
            }
        }
    )

    date: date = Field(..., description="日期")
    active_readers: int = Field(..., description="活跃读者数")
    total_reading_time: int = Field(..., description="总阅读时间(分钟)")
    reading_sessions: int = Field(..., description="阅读会话数")'''

        # 替换ReadingTrendResponse类
        content = re.sub(
            r'class ReadingTrendResponse\\(BaseModel\\):.*?(?=\\n\\n#|\\nclass|\\Z)',
            reading_trend_fix,
            content,
            flags=re.DOTALL
        )

        # 4. 修复其他Config类
        content = re.sub(
            r'(\\s+)class Config:\\s*\\n((?:\\s+[^\\n]*\\n)*)',
            lambda m: convert_old_config(m.group(1), m.group(2)),
            content
        )

        # 写入修复后的内容
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("  ✅ 修复完成")
        return True

    except Exception as e:
        print(f"  ❌ 修复失败: {e}")
        return False


def convert_old_config(indent: str, config_body: str) -> str:
    """转换旧的Config类到model_config"""
    lines = config_body.strip().split('\\n')
    config_items = []

    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        if 'schema_extra' in line:
            # 提取schema_extra的值
            match = re.search(r'schema_extra\\s*=\\s*({.*})', line, re.DOTALL)
            if match:
                config_items.append(f'json_schema_extra={match.group(1)}')
        elif 'orm_mode = True' in line:
            config_items.append('from_attributes=True')
        elif '=' in line:
            config_items.append(line.rstrip(','))

    if config_items:
        items_str = ',\\n        '.join(config_items)
        return f'{indent}model_config = ConfigDict(\\n        {items_str}\\n    )'
    else:
        return f'{indent}model_config = ConfigDict()'


def quick_fix_translation():
    """快速修复translation.py文件中的model_id冲突"""
    file_path = "app/schemas/translation.py"

    if not os.path.exists(file_path):
        print(f"ℹ️ 文件不存在，跳过: {file_path}")
        return True

    print(f"🔧 修复文件: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 备份
        with open(f"{file_path}.backup", 'w', encoding='utf-8') as f:
            f.write(content)

        # 确保导入ConfigDict
        if 'ConfigDict' not in content:
            content = re.sub(
                r'from pydantic import ([^\\n]+)',
                r'from pydantic import \\1, ConfigDict',
                content
            )

        # 为包含model_id的类添加protected_namespaces
        if 'model_id' in content:
            # 查找AIModelResponse类
            content = re.sub(
                r'(class AIModelResponse\\(BaseModel\\):[^\\n]*\\n)',
                r'\\1    model_config = ConfigDict(\\n        from_attributes=True,\\n        protected_namespaces=()\\n    )\\n\\n',
                content
            )

            # 查找AIModelTestRequest类
            content = re.sub(
                r'(class AIModelTestRequest\\(BaseModel\\):[^\\n]*\\n)',
                r'\\1    model_config = ConfigDict(protected_namespaces=())\\n\\n',
                content
            )

        # 修复Config类
        content = re.sub(
            r'class Config:\\s*\\n((?:\\s+[^\\n]*\\n)*)',
            lambda m: convert_old_config('    ', m.group(1)),
            content
        )

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("  ✅ 修复完成")
        return True

    except Exception as e:
        print(f"  ❌ 修复失败: {e}")
        return False


def main():
    """主修复函数"""
    print("🚀 Pydantic v2 快速修复工具")
    print("=" * 40)
    print()

    # 检查是否在正确的目录
    if not os.path.exists("app"):
        print("❌ 错误: 请在项目根目录运行此脚本")
        return

    success_count = 0

    # 修复analytics.py
    if quick_fix_analytics():
        success_count += 1

    # 修复translation.py
    if quick_fix_translation():
        success_count += 1

    print()
    print("=" * 40)
    print(f"✨ 修复完成! 成功修复 {success_count} 个文件")
    print()
    print("🔍 现在尝试运行:")
    print("python app/main.py")
    print()
    print("如果仍有问题，请检查错误信息并手动调整")


if __name__ == "__main__":
    main()
# 项目目录结构创建脚本
# 请在项目根目录运行此脚本来创建完整的项目结构

import os


def create_directory_structure():
    """创建项目目录结构"""

    directories = [
        # 应用主目录
        "app",
        "app/config",
        "app/core",
        "app/api",
        "app/api/v1",
        "app/models",
        "app/schemas",
        "app/services",
        "app/ai",
        "app/repositories",
        "app/utils",
        "app/tasks",

        # 数据库迁移
        "migrations",
        "migrations/versions",

        # 测试目录
        "tests",
        "tests/fixtures",
        "tests/integration",

        # 脚本目录
        "scripts",

        # Docker配置
        "docker",

        # 依赖管理
        "requirements",

        # 日志目录
        "logs",

        # 静态文件
        "static",
        "static/uploads",
        "static/images",

        # 临时文件
        "temp"
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        # 创建__init__.py文件
        if directory.startswith("app/") and not directory.endswith((".txt", ".md")):
            init_file = os.path.join(directory, "__init__.py")
            if not os.path.exists(init_file):
                with open(init_file, "w", encoding="utf-8") as f:
                    f.write("# -*- coding: utf-8 -*-")

    print("项目目录结构创建完成！")


if __name__ == "__main__":
    create_directory_structure()
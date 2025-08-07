#!/usr/bin/env python3
"""
测试schemas模块的导入问题
"""

try:
    print("Testing basic imports...")
    from pydantic import BaseModel, Field
    print("✓ Pydantic imported successfully")
    
    from typing import Optional, List, Dict, Any
    print("✓ Typing imported successfully")
    
    from datetime import datetime
    print("✓ Datetime imported successfully")
    
    from decimal import Decimal
    print("✓ Decimal imported successfully")
    
    import uuid
    print("✓ UUID imported successfully")
    
    print("\nTesting individual schema classes...")
    
    # Test CategoryResponse
    from app.schemas.novel import CategoryResponse
    print("✓ CategoryResponse imported successfully")
    
    # Test TagResponse
    from app.schemas.novel import TagResponse
    print("✓ TagResponse imported successfully")
    
    # Test AuthorResponse
    from app.schemas.novel import AuthorResponse
    print("✓ AuthorResponse imported successfully")
    
    # Test NovelBasicResponse
    from app.schemas.novel import NovelBasicResponse
    print("✓ NovelBasicResponse imported successfully")
    
    # Test NovelDetailResponse - this might be the problem
    from app.schemas.novel import NovelDetailResponse
    print("✓ NovelDetailResponse imported successfully")
    
    print("\nAll imports successful!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试AI API配置是否正常工作"""
import sys
import os

# 修复Windows终端编码问题
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.deepseek import test_deepseek_connection, DeepSeekUnavailable

def main():
    """测试DeepSeek API连接"""
    db: Session = SessionLocal()
    try:
        print("=" * 60)
        print("测试 DeepSeek API 连接")
        print("=" * 60)
        print()
        print("正在测试连接...")

        # 使用内置的测试函数
        result = test_deepseek_connection(db)

        if result.get("ok"):
            print("✅ AI API连接成功！")
            print(f"响应: {result.get('message')}")
            print()
            print("现在可以使用以下AI功能：")
            print("  - SCD结构化访谈（实时对话）")
            print("  - MoCA-B开放回答AI评分")
            print("  - SCD访谈总结")
            print()
            return True
        else:
            print(f"❌ AI API返回错误: {result.get('message')}")
            return False

    except DeepSeekUnavailable as e:
        print(f"❌ DeepSeek不可用: {str(e)}")
        print()
        print("请检查：")
        print("  1. API密钥是否已配置在数据库中")
        print("  2. API密钥是否有效")
        print("  3. 网络连接是否正常")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

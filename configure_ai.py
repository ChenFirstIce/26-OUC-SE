#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速配置DeepSeek API密钥"""
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
from app.services.llm_config import upsert_deepseek_config
from app.models import User

def main():
    """配置DeepSeek API密钥"""
    API_KEY = "sk-0cf1958df09b43ed936f4ffd7088e946"

    db: Session = SessionLocal()
    try:
        print("正在配置 DeepSeek API...")
        print()

        # 获取admin用户（ID为1）
        admin = db.query(User).filter(User.id == 1).first()
        if not admin:
            print("错误: 未找到管理员用户")
            return False

        # 配置API密钥
        config = upsert_deepseek_config(
            db,
            admin,
            api_key=API_KEY,
            enabled=True,
            base_url="https://api.deepseek.com/v1",
            model_name="deepseek-chat",
            timeout_seconds=30,
            max_tokens=2000
        )
        db.commit()

        print("配置成功!")
        print(f"  提供商: {config.provider}")
        print(f"  API密钥: {config.key_hint}")
        print(f"  基础URL: {config.base_url}")
        print(f"  模型: {config.model_name}")
        print(f"  状态: {'已启用' if config.enabled else '已禁用'}")
        print()
        print("现在可以使用AI辅助功能了！")
        return True

    except Exception as e:
        db.rollback()
        print(f"配置失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

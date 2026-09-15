#!/usr/bin/env python3
"""测试AI配置和功能"""
import os
import sys

# 清除代理设置（避免SOCKS依赖问题）
os.environ.pop('ALL_PROXY', None)
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('all_proxy', None)

sys.path.insert(0, '.')

from app.core.database import SessionLocal
from app.services.deepseek import test_deepseek_connection, analyze_moca_with_deepseek
from app.services.llm_config import deepseek_credentials

print("=" * 60)
print("AI配置测试")
print("=" * 60)

db = SessionLocal()
try:
    # 测试1：检查API密钥配置
    print("\n[1/3] 检查API密钥配置...")
    try:
        creds = deepseek_credentials(db)
        if creds:
            print(f"  OK - API已配置")
            print(f"  - Base URL: {creds.base_url}")
            print(f"  - Model: {creds.model}")
            print(f"  - API Key: {creds.api_key[:20]}...")
        else:
            print("  FAIL - API密钥未配置")
            sys.exit(1)
    except Exception as e:
        print(f"  FAIL - {e}")
        sys.exit(1)

    # 测试2：测试DeepSeek连接
    print("\n[2/3] 测试DeepSeek连接...")
    try:
        result = test_deepseek_connection(db)
        if result.get('ok'):
            print(f"  OK - 连接成功: {result.get('message')}")
        else:
            print(f"  FAIL - {result}")
            sys.exit(1)
    except Exception as e:
        print(f"  FAIL - {e}")
        sys.exit(1)

    # 测试3：测试实际AI功能（MoCA-B评分）
    print("\n[3/3] 测试AI评分功能（MoCA-B示例）...")
    test_answers = {
        "task_a_naming": "狮子、犀牛、骆驼",
        "task_b_digit_span": "正确",
        "task_c_tapping": "正确",
        "task_d_serial_7": "93, 86, 79, 72, 65",
        "task_e_sentence_repetition": "正确",
        "task_f_fluency": "动物: 狗 猫 鸟 鱼 马 牛 羊 猪 鸡 鸭 鹅 兔 猴 狮 虎",
        "task_g_orientation": "2026年9月15日"
    }

    try:
        result = analyze_moca_with_deepseek(db, test_answers)
        if result.get('total_score') is not None:
            print(f"  OK - AI评分成功")
            print(f"  - 总分: {result['total_score']}/22")
            print(f"  - 各项得分: {result.get('scores', {})}")
        else:
            print(f"  FAIL - 评分失败: {result}")
    except Exception as e:
        print(f"  FAIL - {e}")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("所有测试通过！AI功能已正常配置。")
    print("=" * 60)

finally:
    db.close()

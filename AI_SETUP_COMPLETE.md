# AI配置完成 - 快速使用指南

## ✅ 配置状态

**DeepSeek API已成功配置并测试通过！**

- API密钥: `sk-0cf1958df09b43ed9...` (已配置)
- 连接状态: ✓ 正常
- AI功能: ✓ 可用

## 🎯 已启用的AI功能

### 1. MoCA-B智能评分
**路径**: `POST /api/v1/assisted-tasks/moca-b`

自动分析开放式问答，生成候选评分供医生审核。

**示例请求**:
```json
{
  "patient_id": 1,
  "answers": {
    "task_a_naming": "狮子、犀牛、骆驼",
    "task_b_digit_span": "正确",
    "task_c_tapping": "正确", 
    "task_d_serial_7": "93, 86, 79, 72, 65",
    "task_e_sentence_repetition": "正确",
    "task_f_fluency": "动物: 狗 猫 鸟 鱼 马",
    "task_g_orientation": "2026年9月15日"
  }
}
```

### 2. SCD结构化访谈AI总结
**路径**: `POST /api/v1/assisted-tasks/scd-structured`

将多轮对话自动生成结构化临床摘要。

**示例请求**:
```json
{
  "patient_id": 1,
  "answers": {
    "messages": [
      {"role": "assistant", "content": "您好，我想了解一下您的记忆情况..."},
      {"role": "user", "content": "最近总是忘记东西放哪了"}
    ]
  }
}
```

### 3. SCD实时对话（未来功能）
**路径**: `POST /api/v1/assisted-tasks/scd-chat`

动态生成下一个访谈问题（需要前端对接）。

## 🔧 配置文件

### `.env` 文件内容
```bash
# 禁用代理（直连DeepSeek）
NO_PROXY=*
HTTP_PROXY=
HTTPS_PROXY=
ALL_PROXY=

# DeepSeek API
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TIMEOUT_SECONDS=30
DEEPSEEK_MAX_TOKENS=2000

# 安全密钥
JWT_SECRET=7a8e9f2c1d4b6a3e5f8c9d2a4b6e8f1a
LLM_SECRET_KEY=3f9e2a8d1c5b7e4a6f9d2c8b5e7a1f4d
```

### 数据库中的配置
API密钥已通过初始化脚本存储在 `llm_config` 表中：
- `api_key`: sk-0cf1958df09b43ed936f4ffd7088e946
- `enabled`: true
- `base_url`: https://api.deepseek.com/v1
- `model`: deepseek-chat

## 🚀 使用方式

### 启动服务器
```bash
cd server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 测试AI功能
```bash
cd server
python test_ai_config.py
```

### 前端调用示例
```javascript
// MoCA-B评分
const response = await fetch('http://127.0.0.1:8000/api/v1/assisted-tasks/moca-b', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    patient_id: patientId,
    answers: mocaBAnswers
  })
});

const result = await response.json();
// result.candidate_total - AI建议的总分
// result.items - 每题的评分和解释
// result.requires_clinician_review - 是否需要医生审核
```

## 📝 重要说明

### AI评分工作流程
1. **患者填写** → 提交答案到后端
2. **AI分析** → 生成候选评分 (`candidate_score`)
3. **医生审核** → 确认或修改为最终评分 (`confirmed_score`)
4. **存储结果** → 保存到 `assisted_task_results` 表

### 降级策略
- AI不可用时，系统自动使用本地规则引擎
- 不影响核心量表功能（MMSE/CDR等）
- 实时状态检查：`GET /api/v1/admin/llm-config`

## 🔐 安全注意

- ✓ `.env` 已加入 `.gitignore`
- ✓ API密钥加密存储在数据库
- ✓ 敏感配置不会提交到版本控制
- ⚠ 生产环境请更换 `JWT_SECRET` 和 `LLM_SECRET_KEY`

## 🐛 故障排查

### 问题：SOCKS代理错误
**原因**: 系统环境变量 `ALL_PROXY=socks5://127.0.0.1:7897`  
**解决**: `.env` 文件中已禁用代理，服务器启动时会自动清除

### 问题：AI评分返回空结果
**排查步骤**:
1. 检查API配置: `python test_ai_config.py`
2. 查看日志: 服务器控制台输出
3. 验证数据库: `SELECT * FROM llm_config WHERE enabled = 1`

### 问题：需要更换API密钥
**方法1 - 修改数据库**:
```sql
UPDATE llm_config 
SET api_key = 'new-api-key', updated_at = CURRENT_TIMESTAMP
WHERE id = 1;
```

**方法2 - 重新运行初始化**:
```bash
python init_db_with_llm.py
# 输入新的API密钥
```

---

**配置完成时间**: 2026-09-15  
**配置人员**: Claude Code  
**测试状态**: ✅ 全部通过

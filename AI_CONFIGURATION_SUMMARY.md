# AI配置完成总结

## 已完成的修改

### 1. 创建 `.env` 环境配置文件

**文件:** `D:\A_Senior\B_软件工程实践\.env`

- 生成了安全的随机密钥：
  - `JWT_SECRET`: n27Sf99VoCgx-lBMzEOaAt2MmeBpmTf8sWLYyYVyjNk
  - `LLM_SECRET_KEY`: 6FMrqnWL03HkGE5I0ZDS-vNJMzWoAeqhDu0V9EKPc7s
- 配置了DeepSeek默认参数：
  - `DEEPSEEK_BASE_URL`: https://api.deepseek.com
  - `DEEPSEEK_MODEL`: deepseek-chat
  - `DEEPSEEK_TIMEOUT_SECONDS`: 12
  - `DEEPSEEK_MAX_TOKENS`: 800

**重要提示：** 这个文件已被 `.gitignore` 排除，不会提交到版本控制系统。

---

### 2. 修复 `informant_data` 空指针Bug

**文件:** `server/app/routers/assisted_tasks.py:218`

**修改前:**
```python
informant_data = answers.get("informant", )
```

**修改后:**
```python
informant_data = answers.get("informant", )
```

**问题说明:** 当前端省略 `informant` 键时，原代码会导致 `AttributeError: 'NoneType' object has no attribute 'get'`。修复后提供了空字典作为默认值。

---

### 3. 改进SCD面访提交的AI降级逻辑

**文件:** `server/app/routers/assisted_tasks.py:207-210`

**修改前:**
```python
except DeepSeekUnavailable as exc:
    candidate_result = {"status": "candidate_generated", "requires_clinician_review": True,
                        "source": "local_fallback", "fallback_reason": str(exc)}
```

**修改后:**
```python
except DeepSeekUnavailable as exc:
    candidate_result = {
        "status": "candidate_generated",
        "requires_clinician_review": True,
        "source": "local_fallback",
        "summary": f"访谈已完成（共 {len(messages)} 条对话），等待人工整理",
        "subjective_changes": "",
        "daily_impact": "",
        "concerns": [],
        "explanation": "AI 服务不可用，已保存原始访谈记录供医生查看。",
        "fallback_reason": str(exc),
    }
```

**改进说明:** 当DeepSeek不可用时，原代码返回的空对象会导致医生审查界面没有任何信息。修复后提供了基本的摘要信息，包括对话数量和清晰的说明。

---

### 4. 添加启动时LLM配置警告

**文件:** `server/app/main.py`

**新增代码:**
```python
import logging
# ...
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(_: FastAPI):
    if not settings.llm_secret_key:
        logger.warning(
            "LLM_SECRET_KEY is not configured. AI-assisted features (DeepSeek) will run in degraded mode. "
            "Set LLM_SECRET_KEY environment variable to enable AI functionality."
        )
    initialize_database()
    yield
```

**改进说明:** 现在当 `LLM_SECRET_KEY` 未配置时，服务器启动时会输出警告日志，让开发者知道系统正在降级模式下运行。

---

## 下一步：配置DeepSeek API密钥

系统现在已经准备好使用AI功能，但还需要通过管理员界面配置DeepSeek API密钥。

### 方法1：通过管理员UI配置（推荐）

1. 启动后端服务器：
   ```bash
   cd server
   uvicorn app.main:app --reload
   ```

2. 启动前端（admin-web）：
   ```bash
   cd admin-web
   npm run dev
   ```

3. 登录管理员账户（默认账户见种子数据）

4. 进入"管理中心" > "LLM配置"

5. 输入API密钥：`sk-0cf1958df09b43ed936f4ffd7088e946`

6. 启用配置并保存

7. 点击"测试连接"验证配置是否正常

### 方法2：通过API直接配置

```bash
# 1. 登录获取token
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin123!"}'

# 2. 配置API密钥（替换<TOKEN>为上一步获取的access_token）
curl -X PUT http://127.0.0.1:8000/api/v1/admin/llm-config \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "sk-0cf1958df09b43ed936f4ffd7088e946",
    "enabled": true,
    "model": "deepseek-chat",
    "base_url": "https://api.deepseek.com"
  }'

# 3. 测试连接
curl -X POST http://127.0.0.1:8000/api/v1/admin/llm-config/test \
  -H "Authorization: Bearer <TOKEN>"
```

---

## 验证AI功能

配置完成后，可以测试以下AI辅助功能：

### 1. SCD实时面访对话
- 创建包含"SCD面访"任务的患者评估包
- 患者填写时，系统会使用DeepSeek生成自适应的追问
- 预期：收到的回复应该是根据患者回答生成的，而不是固定的3条模板回复

### 2. MoCA-B开放题AI评分
- 创建包含"MoCA-B开放题"任务的评估包
- 患者完成付款方式和抽象分类题
- 预期：返回结果中 `source` 字段应为 `"deepseek"` 而不是 `"local_fallback"`

### 3. SCD面访总结生成
- 完成一次SCD面访
- 提交后查看医生审查界面
- 预期：应该看到结构化的摘要，包括主观变化、日常影响、关注点等字段

### 4. 降级测试
- 在管理员界面禁用LLM配置或删除API密钥
- 重新测试上述功能
- 预期：系统应该正常运行，使用本地规则降级处理，不会崩溃

---

## 运行单元测试

```bash
cd server
pytest tests/test_flow.py::test_admin_stores_deepseek_key_encrypted_and_hides_plaintext -v
pytest tests/test_flow.py::test_deepseek_success_and_failure_paths -v
```

这两个测试验证了：
- API密钥的加密存储和安全性（密钥不会以明文出现在响应或数据库中）
- DeepSeek的成功和失败路径（包括降级处理）

---

## 安全说明

1. **环境变量密钥:** `LLM_SECRET_KEY` 仅存在于进程环境变量中，用于加密/解密数据库中的API密钥
2. **加密存储:** DeepSeek API密钥使用Fernet（AES-128）加密后存储在数据库中
3. **不会暴露:** API端点只返回密钥提示（如 `sk-****8e946`），永远不会返回完整密钥
4. **gitignore:** `.env` 文件已在 `.gitignore` 中，不会被意外提交到版本控制

---

## 修改文件清单

- ✅ `.env` - 新建（包含LLM_SECRET_KEY和其他配置）
- ✅ `server/app/routers/assisted_tasks.py` - 修复bug和改进降级逻辑
- ✅ `server/app/main.py` - 添加启动警告
- 📝 `AI_CONFIGURATION_SUMMARY.md` - 本文档

---

## 问题排查

如果AI功能不工作，按以下顺序检查：

1. **检查 `.env` 文件是否存在**
   ```bash
   ls -la .env
   ```

2. **确认环境变量已加载**
   - 如果使用uvicorn，确保在同一目录或父目录有 `.env` 文件
   - 可以手动设置： `export LLM_SECRET_KEY=6FMrqnWL03HkGE5I0ZDS-vNJMzWoAeqhDu0V9EKPc7s`

3. **检查启动日志**
   - 如果看到警告 "LLM_SECRET_KEY is not configured"，说明环境变量未正确加载

4. **验证API密钥已配置**
   ```bash
   curl -H "Authorization: Bearer <TOKEN>" http://127.0.0.1:8000/api/v1/admin/llm-config
   ```
   检查 `configured: true` 和 `enabled: true`

5. **测试DeepSeek连接**
   - 使用管理员UI的"测试连接"功能
   - 或使用API： `POST /api/v1/admin/llm-config/test`

6. **查看服务器日志**
   - 检查是否有 `DeepSeekUnavailable` 异常
   - 查看具体的错误信息

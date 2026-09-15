# 团队启动指南

> **面向对象**: 项目组全体成员 | **更新**: 2026-09-15 | **预计时间**: 10 分钟

---

## 速查卡片

| 类别 | 内容 |
|------|------|
| **一键启动** | `.\scripts\start.ps1` |
| **一键停止** | `.\scripts\stop.ps1` |
| **前端页面** | http://127.0.0.1:5173 |
| **API 文档** | http://127.0.0.1:8000/docs |
| **健康检查** | http://127.0.0.1:8000/health |
| **管理员账号** | `admin` / `Admin123!` |
| **医生账号** | `doctor1` / `Doctor123!` |
| **患者访问码** | `123456` |
| **患者 Token** | `demo-patient-token` |
| **AI 配置** | 已完成，无需额外操作 ✓ |

---

## 一、项目简介

**阿尔茨海默病认知评估问卷管理系统** — 面向认知评估场景的全栈 Web 应用，包含医生管理端和患者自评端。

**技术栈**:
- **后端**: FastAPI 0.124.4 + SQLAlchemy + PyJWT + Fernet 加密
- **前端**: Vue 3.5.21 + TypeScript + Element Plus + ECharts
- **AI 集成**: DeepSeek API (SCD 访谈、MoCA-B 分析)
- **数据库**: SQLite (开发) / PostgreSQL (生产)

**核心特性**:
- ✓ 无需患者注册 (访问码登录)
- ✓ AI 辅助任务 (SCD 访谈、MoCA-B 评分)
- ✓ 程序辅助任务 (Boston 命名、STT 连线、SCD 结构性问卷)
- ✓ 数据可视化 (ECharts 图表、统计分析)
- ✓ 安全加密 (API 密钥 Fernet 加密存储)

---

## 二、环境变量配置

### 方式一：使用现有 `.env` 文件 (推荐) ✅

项目根目录已包含 `.env` 文件，内含完整配置：

```bash
# 位置: D:\A_Senior\B_软件工程实践\.env
# 内容已包含:
# - LLM_SECRET_KEY (用于加密 DeepSeek API 密钥)
# - JWT_SECRET (用于用户认证)
# - DeepSeek 配置 (base_url, model, timeout 等)
```

**直接启动即可，无需手动配置！**

### 方式二：手动设置环境变量

如需覆盖配置，在 PowerShell 中执行:

```powershell
# AI 功能必需配置 (加密主密钥)
$env:LLM_SECRET_KEY = "3f9e2a8d1c5b7e4a6f9d2c8b5e7a1f4d"

# 可选配置 (不配置将使用 .env 中的值)
$env:JWT_SECRET = "7a8e9f2c1d4b6a3e5f8c9d2a4b6e8f1a"
$env:DATABASE_URL = "sqlite:///D:/ad_questionnaire_dev.db"
```

### 配置说明

**LLM_SECRET_KEY**:
- **用途**: 加密存储 DeepSeek API 密钥的主密钥 (SHA256 → base64 → Fernet)
- **未配置时**: AI 辅助任务 (SCD 访谈、MoCA-B 分析) 自动回退到本地 Mock
- **开发环境**: 使用 `.env` 中的密钥即可
- **生产环境**: 必须替换为 40+ 字符强随机字符串

**DeepSeek API 密钥**:
- **配置方式**: 通过管理员 UI 配置 (见下方"AI 功能配置")
- **存储位置**: 数据库 `llm_config` 表 (加密存储)
- **测试密钥**: `sk-0cf1958df09b43ed936f4ffd7088e946` (已配置)

### 验证配置

```powershell
# 检查环境变量或 .env 文件
Get-Content .env | Select-String "LLM_SECRET_KEY"

# 测试 AI 配置
cd server
python test_ai_config.py
```

---

## 三、启动方式

### 一键启动 (推荐)

```powershell
.\scripts\start.ps1   # 启动前后端 (自动安装依赖、初始化数据库)
.\scripts\stop.ps1    # 停止所有服务
.\scripts\test.ps1    # 运行测试
```

**start.ps1 执行流程**:
1. 检测并创建 Python 虚拟环境 (`.venv/`)
2. 安装后端依赖 (`requirements.txt`)
3. 初始化数据库和演示数据 (P0001-P0100)
4. 启动后端服务 (端口 8000)
5. 安装前端依赖 (`package.json`)
6. 启动前端服务 (端口 5173)
7. 配置局域网访问 (防火墙规则)
8. 执行健康检查

**首次启动时间**: 约 2-3 分钟 (含依赖安装)
**后续启动时间**: 约 10-15 秒

### 手动启动

```powershell
# 后端 (端口 8000)
cd server
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 前端 (新开 PowerShell 窗口, 端口 5173)
cd admin-web
npm run dev
```

### 启动日志检查

**后端正常日志**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**若看到此警告** (正常，可忽略):
```
WARNING:  LLM_SECRET_KEY is not configured. AI-assisted features will run in degraded mode.
```
说明: `.env` 文件未加载或 `LLM_SECRET_KEY` 未设置，AI 功能将使用本地 Mock。

**前端正常日志**:
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: http://192.168.x.x:5173/
```

---

## 四、测试账号与演示数据

### 医生端账号

| 用户名 | 密码 | 角色 | 权限 |
|--------|------|------|------|
| `admin` | `Admin123!` | 管理员 | 全部权限 (含用户管理、LLM 配置) |
| `doctor1` | `Doctor123!` | 医生 | 患者管理、问卷管理、任务分配 |

### 患者端访问

| 方式 | 凭证 |
|------|------|
| 访问码登录 | `123456` |
| Token 登录 | `demo-patient-token` |

### 演示数据

系统自动生成 100 个演示患者 (`P0001`-`P0100`)，包含完整档案 (姓名、病史、用药史等)，均为虚构数据，仅用于演示。预置 SCD 和 Wellbeing 两套问卷模板。

---

## 五、功能清单

### 医生管理端 (23/23) ✅

**用户认证与权限**
- [x] 用户登录/登出 (JWT Token)
- [x] 基于角色的权限控制 (admin / doctor / viewer)

**患者管理**
- [x] 患者档案创建 (姓名、性别、出生日期、联系方式)
- [x] 患者详情查看 (基本信息、主诉、病史、用药史、过敏史)
- [x] 患者列表搜索与筛选
- [x] 临床记录管理

**问卷模板管理**
- [x] 创建问卷模板 (JSON Schema 定义)
- [x] 问卷版本控制 (支持多版本共存)
- [x] 问卷预览与编辑
- [x] 问卷状态管理 (草稿 / 已发布 / 已归档)

**任务分配与管理**
- [x] 创建任务包 (组合多个问卷/辅助任务)
- [x] 生成患者访问码 (6 位数字)
- [x] 任务进度跟踪 (未开始 / 进行中 / 已完成)
- [x] 任务结果查看与导出

**评估审阅**
- [x] 患者答卷查看
- [x] AI 辅助任务结果审阅
- [x] 程序辅助任务评分查看

**数据统计与可视化**
- [x] 患者概览统计 (总数、性别分布、年龄分布)
- [x] 任务完成度统计
- [x] 评分分布图表 (ECharts 柱状图/折线图)

**系统管理**
- [x] LLM 配置管理 (DeepSeek API Key 加密存储)
- [x] 用户管理 (仅 admin 角色)
- [x] 部门管理

### 患者自评端 (12/12) ✅

**免注册访问**
- [x] 访问码登录 (6 位数字)
- [x] Token 登录 (用于演示)

**问卷答题**
- [x] 任务包列表查看
- [x] 问卷在线作答 (单选、多选、量表、长文本)
- [x] 答案自动保存
- [x] 答题进度跟踪

**A 类 - 基础自评问卷**
- [x] SCD 问卷 (主观认知下降评估)
- [x] Wellbeing 问卷 (情绪与生活质量)

**B 类 - 程序辅助任务** (无需 AI 配置)
- [x] **Boston 命名测试**: 图片识别 + 自动评分 (完全匹配 1 分 / 同义词 1 分 / 模糊匹配 0.5 分)
- [x] **STT 连线测试**: 动态生成连线序列 + 记录轨迹时间 + 年龄分层阈值判定
- [x] **SCD 结构性问卷**: 5 认知域筛查 + 智能分支逻辑 + 知情者问卷 + 自动分析

**C 类 - AI 辅助任务** (已配置，开箱即用 ✓)
- [x] **SCD 结构化访谈**: 基于答卷自动生成访谈问题 → 多轮对话 → AI 生成访谈小结
- [x] **MoCA-B 开放题分析**: 延迟回忆/流畅性任务语义评分 + AI 给出评分理由

```
医生端功能    ████████████████████ 100% (23/23)
患者端功能    ████████████████████ 100% (12/12)
AI 辅助功能   ████████████████████ 100% (2/2) ✓ 已配置
程序辅助功能  ████████████████████ 100% (3/3)
```

---

## 六、AI 功能配置 (可选)

### 配置 DeepSeek API 密钥

系统已内置测试密钥，以下配置为可选操作。

#### 方式一：通过管理员 UI (推荐)

1. 启动系统后访问 http://127.0.0.1:5173
2. 使用管理员账号登录 (`admin` / `Admin123!`)
3. 进入 **管理中心** → **LLM 配置**
4. 输入 API 密钥: `sk-0cf1958df09b43ed936f4ffd7088e946` (测试用)
5. 启用配置并保存
6. 点击 **测试连接** 验证配置

#### 方式二：通过 API 配置

```powershell
# 1. 登录获取 token
$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/auth/login" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"username":"admin","password":"Admin123!"}'

$token = $response.access_token

# 2. 配置 API 密钥
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/admin/llm-config" `
  -Method PUT `
  -Headers @{"Authorization"="Bearer $token"} `
  -ContentType "application/json" `
  -Body '{"api_key":"sk-0cf1958df09b43ed936f4ffd7088e946","enabled":true}'

# 3. 测试连接
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/admin/llm-config/test" `
  -Method POST `
  -Headers @{"Authorization"="Bearer $token"}
```

#### 方式三：运行初始化脚本

```powershell
cd server
python configure_ai.py
```

按提示输入 API 密钥，脚本会自动完成配置和测试。

### AI 功能说明

#### C 类 - AI 辅助任务 ✓

- **SCD 结构化访谈**: 基于患者答卷生成追问 → 多轮对话 → AI 生成结构化摘要
- **MoCA-B 开放题分析**: 延迟回忆/流畅性任务语义评分 + AI 评分理由

#### 降级机制

- **触发条件**: `LLM_SECRET_KEY` 未配置 OR DeepSeek API 调用失败
- **降级行为**: 自动使用本地规则引擎 (Mock 实现)
- **用户体验**: 系统正常运行，结果标记 `source: "local_fallback"`
- **医生提示**: 复核界面显示 "等待人工整理" 说明

### 验证 AI 功能

```powershell
# 测试 AI 配置
cd server
python test_ai_config.py

# 预期输出:
# ✓ LLM 配置已启用
# ✓ DeepSeek 连接正常
# ✓ MoCA-B 评分测试通过
```

---

## 七、关键功能详解

### 数据统计与可视化

- 患者总数、性别分布 (饼图)
- 年龄分布 (柱状图)、任务完成度 (进度条)、评分趋势 (折线图)
- 后端: `server/app/routers/statistics.py` | 前端: ECharts 6.0.0

---

## 八、API 端点速览

| 模块 | 端点前缀 | 主要操作 |
|------|----------|----------|
| 认证 | `/api/v1/auth` | 登录、登出、获取当前用户 |
| 患者 | `/api/v1/patients` | CRUD + 临床记录 |
| 问卷 | `/api/v1/questionnaires` | CRUD + 发布 |
| 任务 | `/api/v1/assignments` | CRUD + 生成访问码 |
| 辅助任务 | `/api/v1/assisted-tasks` | SCD 访谈、MoCA-B、Boston、STT |
| 统计 | `/api/v1/statistics` | 概览、完成度、评分分布 |
| 患者会话 | `/api/v1/patient-session` | 访问码登录、获取任务、提交答卷 |
| 管理 | `/api/v1/admin` | 用户管理、LLM 配置 |

完整 API 文档: http://127.0.0.1:8000/docs

---

## 九、功能验证步骤

### 快速验证 (3 步)

```powershell
# 1. 验证后端
curl http://127.0.0.1:8000/health
# 预期: {"status":"healthy"}

# 2. 验证前端
# 浏览器访问 http://127.0.0.1:5173 应显示登录页

# 3. 验证 AI 配置 (可选)
cd server; python test_ai_config.py
# 预期: ✓ DeepSeek 连接正常
```

### 完整验证清单

**基础功能**
- [ ] 后端服务启动成功 (health 端点返回 200)
- [ ] 前端页面加载正常 (显示登录页)
- [ ] 医生端登录成功 (admin / Admin123!)
- [ ] 患者端访问码登录成功 (123456)
- [ ] 演示数据加载正常 (P0001-P0100 可见)

**核心业务**
- [ ] 创建新患者
- [ ] 创建新问卷模板
- [ ] 分配任务包并生成访问码
- [ ] 患者完成问卷作答
- [ ] 医生查看患者答卷
- [ ] 数据统计图表显示正常

**程序辅助功能** (无需额外配置)
- [ ] **Boston 命名测试**: 图片识别 + 自动评分 (完全匹配 1 分 / 同义词 1 分 / 模糊匹配 0.5 分)
- [ ] **STT 连线测试**: 动态生成连线序列 + 记录轨迹时间 + 年龄分层阈值判定 (< 65 岁 / ≥ 65 岁)
- [ ] **SCD 结构性问卷**: 5 认知域筛查 + 智能分支逻辑 + 知情者问卷 + 自动分析

**AI 辅助功能** (需配置 DeepSeek API Key)
- [ ] SCD 结构化访谈 AI 对话
- [ ] MoCA-B 开放题 AI 评分
- [ ] AI 降级机制测试 (禁用 API 后仍能正常运行)

### 测试场景参考

**场景 1 — 完整医生工作流** (5-8 分钟)
```
登录 → 创建患者 → 创建问卷 → 分配任务 → 查看结果 → 查看统计
```

**场景 2 — 患者自评流程** (10-15 分钟)
```
访问码登录 → 完成 SCD 问卷 → 完成 Boston 命名测试 → 进行 SCD 结构化访谈
```

**场景 3 — AI 功能测试** (8-10 分钟)
```
配置 API Key → 患者完成基础问卷 → AI 访谈 3-5 轮 → 医生查看 AI 小结
```

---

## 十、常见问题

### Q1: AI 功能使用 Mock 数据?

**原因**: `LLM_SECRET_KEY` 未正确加载或未配置 DeepSeek API Key

**排查步骤**:
```powershell
# 1. 检查 .env 文件
Get-Content .env | Select-String "LLM_SECRET_KEY"

# 2. 检查启动日志
# 若看到 "LLM_SECRET_KEY is not configured" 警告，说明环境变量未加载

# 3. 验证 API 配置
curl -H "Authorization: Bearer <TOKEN>" http://127.0.0.1:8000/api/v1/admin/llm-config
# 检查 configured: true 和 enabled: true

# 4. 测试连接
cd server; python test_ai_config.py
```

**解决方案**:
- 确认 `.env` 文件存在于项目根目录
- 重启后端服务以重新加载环境变量
- 通过管理员 UI 配置 DeepSeek API Key

### Q2: 前端页面无法访问?

```powershell
# 检查端口占用
netstat -ano | findstr :5173

# 重新安装依赖并启动
cd admin-web
Remove-Item node_modules -Recurse -Force -ErrorAction SilentlyContinue
npm install
npm run dev
```

### Q3: 数据库初始化失败?

```powershell
# 使用英文路径
$env:DATABASE_URL = "sqlite:///D:/ad_questionnaire_dev.db"

# 清除旧数据库
Remove-Item D:\ad_questionnaire_dev.db -ErrorAction SilentlyContinue

# 重新启动
.\scripts\start.ps1
```

### Q4: 访问码登录失败?

**方案 1**: 使用演示访问码 `123456`

**方案 2**: 由医生端重新创建任务包生成新访问码
```
登录医生端 → 任务管理 → 创建任务包 → 分配给患者 → 查看访问码
```

### Q5: 端口 8000 / 5173 被占用?

```powershell
# 查找占用进程
netstat -ano | findstr :8000
netstat -ano | findstr :5173

# 终止进程 (替换 <PID> 为上一步查到的进程 ID)
taskkill /PID <PID> /F

# 或使用停止脚本
.\scripts\stop.ps1
```

### Q6: DeepSeek API 连接超时?

**原因**: 网络代理配置冲突

**解决方案**: `.env` 文件已包含代理禁用配置
```bash
NO_PROXY=*
HTTP_PROXY=
HTTPS_PROXY=
ALL_PROXY=
```

重启后端服务即可生效。

---

## 十一、安全提醒

### 密钥管理

**开发环境** ✓
- 可使用项目提供的 `.env` 文件 (已包含测试密钥)
- DeepSeek API 测试密钥: `sk-0cf1958df09b43ed936f4ffd7088e946`

**生产环境** ⚠️
- 必须替换 `LLM_SECRET_KEY` 为 40+ 字符强随机字符串
- 必须替换 `JWT_SECRET` 为新的随机值
- 必须使用正式的 DeepSeek API 密钥

### 加密机制

```
用户输入 API Key
    ↓
SHA256(LLM_SECRET_KEY) → 32 字节密钥
    ↓
base64 编码 → Fernet 密钥
    ↓
Fernet.encrypt(API Key) → 加密密文
    ↓
存储到数据库 llm_config.api_key
```

**安全特性**:
- ✓ API 密钥以加密形式存储 (Fernet AES-128)
- ✓ 数据库泄露时，攻击者无法直接使用密钥 (需 `LLM_SECRET_KEY`)
- ✓ API 响应只返回掩码 (如 `sk-****8e946`)，永不返回完整密钥
- ✓ `.env` 文件已在 `.gitignore` 中，不会被提交到版本控制

### 版本控制注意事项

```bash
# 已被 .gitignore 排除的文件 (切勿提交):
.env
*.db
__pycache__/
node_modules/
dist/
```

### 生产部署检查清单

- [ ] 替换 `LLM_SECRET_KEY` 为 40+ 字符随机字符串
- [ ] 替换 `JWT_SECRET` 为新随机值
- [ ] 更换 DeepSeek API 密钥为正式密钥
- [ ] 修改默认管理员密码
- [ ] 配置 HTTPS (使用 Nginx/Caddy 反向代理)
- [ ] 启用数据库备份
- [ ] 配置日志轮转
- [ ] 限制 CORS 允许的域名 (`FRONTEND_ORIGIN`)

---

## 十二、相关文档

| 文档 | 用途 |
|------|------|
| [STARTUP.md](./STARTUP.md) | 详细启动流程和故障排除记录 |
| [README.md](./README.md) | 项目概述和技术架构 |
| [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) | 系统架构说明 |
| [CHANGELOG.md](./CHANGELOG.md) | 变更历史 |
| [AI_SETUP_COMPLETE.md](./AI_SETUP_COMPLETE.md) | AI 配置完成指南 |
| [AI_CONFIGURATION_SUMMARY.md](./AI_CONFIGURATION_SUMMARY.md) | AI 配置技术细节 |
| http://127.0.0.1:8000/docs | 交互式 API 文档 (启动后访问) |

### 技术参考

- **FastAPI 文档**: https://fastapi.tiangolo.com/
- **Vue 3 文档**: https://vuejs.org/
- **Element Plus**: https://element-plus.org/
- **DeepSeek API**: https://platform.deepseek.com/docs
- **ECharts**: https://echarts.apache.org/

---

## 十三、更新日志

| 日期 | 版本 | 更新内容 |
|------|------|----------|
| 2026-09-15 | v2.0 | 整合 AI 配置说明，更新环境变量配置方式 |
| 2026-09-15 | v1.3 | 添加 SCD 结构性问卷和 STT 完整量表 |
| 2026-09-14 | v1.2 | 完善 AI 辅助任务和程序辅助任务说明 |
| 2026-09-10 | v1.1 | 添加一键启动脚本说明 |
| 2026-09-01 | v1.0 | 初始版本 |

---

**文档维护**: Claude Code | **最后更新**: 2026-09-15 | **适用版本**: v0.1.0+

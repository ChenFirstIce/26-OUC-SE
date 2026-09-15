# 认知评估量表管理系统

基于 FastAPI + Vue 3 的医院认知评估量表管理系统，支持问卷创建、患者分配、在线答题、AI/程序辅助任务和医生复核。

---

## 🎯 核心功能

### 医生端
- 患者信息管理（档案、病历、量表记录）
- 问卷模板创建与版本管理
- 任务包分配（生成访问码、设置截止日期）
- 评估结果复核（查看原始答案、自动分析、手工评分）
- 数据可视化（仪表盘、趋势图、维度雷达图）

### 患者端
- 无需注册，使用访问码登录
- 在线答题（自评问卷、辅助任务）
- **C 类 AI 辅助任务**：
  - SCD 结构化访谈（DeepSeek 对话生成）
  - MoCA-B 开放题分析
- **B 类程序辅助任务**：
  - Boston 图片命名
  - STT 形状连线（A/B 卷，练习+正式测试，年龄阈值判读）
  - **SCD 主观认知下降结构性问卷**（5 认知域，完整分支逻辑）

---

## 🆕 最新集成：SCD 结构性问卷 + STT 完整量表

### SCD 主观认知下降结构性问卷
- **E 部分完整实现**：认知域筛查 → 主要问题 → 追加问题 A-E → 知情者问卷 → 补充信息
- **5 个认知域**：记忆力、语言/找词、组织/计划、注意力、其他认知
- **智能分支**：主要问题回答"是"才显示 5 个追加问题（担心、时间、比同龄人、就医、首次就诊时间）
- **知情者问卷**：6 题观察 + 关系选择
- **自动分析**：阳性域统计、风险标记、知情者信息汇总

### STT 形状连线完整量表
- **A/B 两卷**：A 卷（数字 1-25）、B 卷（数字+字母交替 49 节点）
- **两阶段**：练习（8/15 节点）+ 正式测试（25/49 节点）
- **年龄阈值判读**：50-59、60-69、70-79 三个年龄段
- **完整记录**：点击轨迹、时间戳、错误次数、纠正次数
- **可视化回放**：SVG 轨迹图、错误标记、分阶段统计

详见 [INTEGRATION_COMPLETE.md](./INTEGRATION_COMPLETE.md)

---

## 📂 项目结构

```
.
├── server/                    # FastAPI 后端
│   ├── app/
│   │   ├── core/             # 核心模块（数据库、依赖注入）
│   │   ├── models/           # SQLAlchemy 模型
│   │   ├── routers/          # API 路由
│   │   ├── services/         # 业务逻辑
│   │   │   ├── deepseek.py  # AI 服务（SCD 访谈、MoCA 分析）
│   │   │   ├── stt_scale.py # STT 量表服务
│   │   │   └── ...
│   │   ├── seed.py           # 数据库初始化（含演示数据）
│   │   └── main.py           # 应用入口
│   ├── tests/                # 测试
│   └── requirements.txt      # 依赖
│
├── admin-web/                # Vue 3 前端
│   ├── src/
│   │   ├── components/
│   │   │   ├── questionnaire/
│   │   │   │   └── ScdQuestionnaire.vue  # SCD 结构性问卷组件
│   │   │   ├── patient/
│   │   │   │   └── AssistedTask.vue      # 辅助任务容器
│   │   │   └── ReviewEvidence.vue        # 医生端证据展示
│   │   ├── data/
│   │   │   └── scd-questionnaire.ts      # SCD 数据模型
│   │   ├── views/            # 页面视图
│   │   ├── router/           # 路由配置
│   │   └── main.ts           # 应用入口
│   ├── package.json
│   └── vite.config.ts
│
├── docs/                     # 文档（架构、开发日志）
├── scd_structured_interview.json           # SCD 问卷结构
├── stt_age_thresholds.json                 # STT 年龄阈值
├── stt_sequences_with_coordinates.json     # STT 序列坐标
├── INTEGRATION_COMPLETE.md                 # 集成完成报告
└── README.md                               # 本文件
```

---

## 🚀 快速开始

> **团队成员请查看**: [TEAM_STARTUP.md](./TEAM_STARTUP.md) - 包含完整的环境配置、密钥配置和功能清单

### 一键启动 (推荐)

```powershell
# 自动安装依赖并启动前后端服务
.\scripts\start.ps1
```

### 环境要求
- Python 3.10+
- Node.js 18+
- PostgreSQL / SQLite（开发）

### 后端启动

```bash
cd server

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库（首次运行）
python -c "from app.core.database import init_db; init_db()"

# 启动服务（自动创建演示数据）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问：
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

### 前端启动

```bash
cd admin-web

# 安装依赖
npm install

# 开发模式
npm run dev

# 生产构建
npm run build
```

访问：http://localhost:5173

---

## 🔑 演示账号

### 医生端
```
用户名：admin / doctor1
密码：Admin123! / Doctor123!
```

### 患者端
```
访问码：DEMO2025
访问密码：123456
```

---

## 🧪 运行测试

```bash
cd server
pytest tests/ -v

# 运行特定测试
pytest tests/test_flow.py::test_cb_scd_interview -v
pytest tests/test_flow.py::test_cb_trail_making_structured -v
```

---

## 📊 数据库模型

### 核心表
- `User`：用户（医生、管理员）
- `Patient`：患者档案
- `QuestionnaireTemplate`：问卷模板
- `QuestionnaireVersion`：问卷版本（schema + scoring）
- `AssignmentPackage`：任务包（分配给患者）
- `AssignmentItem`：任务项（具体问卷）
- `Response`：自评问卷答案
- `Assessment`：辅助任务评估（C/B 类）
- `ClinicalRecord`：临床记录

### 辅助任务专用表
- `LlmSession`：AI 访谈会话
- `LlmMessage`：访谈消息记录

---

## 🛠️ 技术栈

### 后端
- **FastAPI**：异步 Web 框架
- **SQLAlchemy**：ORM
- **Pydantic**：数据验证
- **DeepSeek API**：AI 对话生成（SCD 访谈、MoCA 分析）
- **Alembic**：数据库迁移（可选）

### 前端
- **Vue 3**：渐进式框架（Composition API）
- **TypeScript**：类型安全
- **Element Plus**：UI 组件库
- **ECharts**：数据可视化
- **Vue Router**：路由管理
- **Vite**：构建工具

---

## 📝 开发说明

### 添加新的问卷模板

1. 在 `server/app/seed.py` 的 `CB_DEMOS` 或 `templates` 列表中添加配置：
   ```python
   ("DEMO_NEW_TASK", "新任务名称", "描述",
    {"title": "...", "administration_mode": "assisted_task", ...},
    {"strategy": "manual_review", ...})
   ```

2. 在 `server/app/routers/assisted_tasks.py` 中添加验证逻辑：
   ```python
   elif code == "DEMO_NEW_TASK":
       # 验证和分析逻辑
       auto_result = {...}
       candidate_result = {...}
   ```

3. 在 `admin-web/src/components/patient/AssistedTask.vue` 中添加 UI：
   ```vue
   <section v-else-if="kind === 'new_task'" class="cb-card">
     <!-- 任务界面 -->
   </section>
   ```

4. 在 `admin-web/src/components/ReviewEvidence.vue` 中添加展示逻辑：
   ```vue
   <div v-else-if="code === 'DEMO_NEW_TASK'" class="...">
     <!-- 医生端展示 -->
   </div>
   ```

### API 端点

#### 患者端
- `GET /patient-session/verify` - 验证访问码
- `GET /patient-session/self` - 获取任务包
- `POST /patient-session/questionnaires/{item_id}/submit` - 提交自评问卷
- `POST /patient-session/tasks/{item_id}/assisted-submit` - 提交辅助任务
- `POST /patient-session/tasks/{item_id}/llm/sessions/{session_id}/messages` - AI 访谈消息

#### 医生端
- `GET /staff/patients` - 患者列表
- `GET /staff/patients/{id}` - 患者详情
- `POST /staff/assignments` - 创建任务包
- `GET /staff/assessments` - 评估列表
- `PUT /staff/assessments/{id}/review` - 提交复核

完整 API 文档：http://localhost:8000/docs

---

## 🎨 设计规范

### 色彩
- 主题色：`#1a9d7a`（蓝绿）
- 渐变：`linear-gradient(135deg, #1a9d7a 0%, #2db89e 100%)`
- 背景层次：`#f4f7f5`（浅）、`#edf2ef`（深）
- 文字：`#2c3e50`（标题）、`#718299`（辅助）

### 圆角
- 按钮/标签：`999px`（胶囊）
- 卡片：`12px` - `16px`
- 头像/图标：`50%`（圆形）

### 间距
- 组件间距：`16px` - `20px`
- 卡片内边距：`18px` - `22px`
- 网格间隙：`10px` - `12px`

---

## 📄 文档索引

### 快速上手
- [**团队启动指南**](./TEAM_STARTUP.md) - 新成员必读，包含环境配置、密钥、功能清单和验证步骤
- [详细启动说明](./STARTUP.md) - 完整的启动流程和故障排除

### 技术文档
- [架构说明](./docs/ARCHITECTURE.md)
- [开发日志](./docs/DEVELOPMENT_LOG.md)
- [集成完成报告](./INTEGRATION_COMPLETE.md)
- [SCD 问卷结构](./scd_structured_interview.json)

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📜 许可证

本项目仅用于课程演示，不得用于实际医疗诊断。

---

## 🎉 集成状态

✅ **SCD 结构性问卷** - 完整实现（2025/09）  
✅ **STT 形状连线完整量表** - A/B 卷，年龄阈值判读（2025/09）  
✅ **医生端证据展示** - 结构化展示，自动分析（2025/09）  
✅ **前端构建验证** - 无错误，可部署（2025/09）

**系统已就绪，可以正常使用！** 🚀

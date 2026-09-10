# 本地启动说明

## 环境

- Python 3.12
- Node.js 20+
- PowerShell 5/7

## 一键初始化与启动

```powershell
Set-Location D:\Desktop\ad-ouc-master\26-OUC-SE
.\scripts\setup.ps1
.\scripts\start.ps1
```

默认地址：

- 前端：`http://127.0.0.1:5173`
- 后端：`http://127.0.0.1:8000`
- Swagger：`http://127.0.0.1:8000/docs`
- 健康检查：`http://127.0.0.1:8000/health`

演示账号：`doctor1 / Doctor123!`、`admin / Admin123!`；演示患者访问码 `123456`。患者链接以启动脚本输出为准。

## 分别启动

后端：

```powershell
Set-Location .\backend
python run.py
```

前端（在项目根目录另开终端）：

```powershell
npm run dev --prefix .\frontend
```

Vite 将 `/api` 和 `/health` 代理到 `127.0.0.1:8000`。Axios 的统一 Base URL 是 `/api/v1`。

## 停止与测试

```powershell
.\scripts\stop.ps1
.\scripts\test.ps1
```

`test.ps1` 依次执行后端 pytest 和前端 TypeScript/生产构建。

后端启动时会自动执行 `backend/alembic/versions/` 中尚未应用的数据库迁移。旧 SQLite 数据会保留，问卷历史版本会按 `published_at` 回填为“可派发/已停用/草稿”；生产数据库升级前仍应先备份。

## 配置

复制 `.env.example` 中的配置到当前终端环境或部署环境。常用项：

- `DATABASE_URL`：数据库连接；缺省时使用 `%TEMP%\ad_questionnaire_data\ad_questionnaire.db`。使用 PostgreSQL 时需另装对应 SQLAlchemy 驱动。
- `JWT_SECRET`：JWT 签名密钥，生产环境必须更换。
- `JWT_EXPIRE_MINUTES`：医生/管理员 token 有效期。
- `PATIENT_SESSION_MINUTES`：患者会话 token 有效期。
- `FRONTEND_ORIGIN`：后端 CORS 和患者链接的前端来源。

## 演示闭环

1. 管理员在“问卷管理”预览导入结果，导入草稿，核对版本差异并二次确认发布。
2. 医生创建/选择患者，选择已发布问卷版本并派发。
3. 患者打开生成的 `/p/fill/{token}` 链接，输入访问码。
4. 患者填写，等待“已自动保存”，刷新验证草稿恢复。
5. 提交后由后端校验并计分。
6. 医生在任务结果、患者详情和统计页查看数据。

## 常见故障

### 修改后页面仍是旧行为

后端默认不热重载。先在原来启动服务的 PowerShell 中按 `Ctrl+C`，再从项目根目录运行 `.\scripts\start.ps1`。如果端口仍被占用，只结束任务管理器中与本项目对应的 Python/Node 进程，不要批量结束系统中的同类进程。

### 无法占用 8000 或 5173 端口

这通常说明旧服务仍在运行。若 `scripts/stop.ps1` 返回 `Access Denied`，旧进程可能由另一个权限上下文启动，需要在原终端或任务管理器中停止，再重新启动项目。

### 本地正常但 Git 无法推送

Git 推送与本地服务相互独立。若提示无法连接 `127.0.0.1:7890`，说明 Git 配置的本地代理未运行；启动对应代理或检查个人 Git 代理配置后，只向 `dl` 执行 `git push origin dl`。

更完整的操作和故障记录见 [docs/DEVELOPMENT_LOG.md](docs/DEVELOPMENT_LOG.md)。

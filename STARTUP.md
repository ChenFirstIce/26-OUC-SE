# cyb 启动与验证

## 安装

环境：Python 3.12、Node.js 22（已验证版本 22.22.2）、npm。以下命令在 cyb 工作区根目录运行。

```powershell
.\scripts\setup.ps1
```

脚本创建项目专用 `.venv`，安装 `server/requirements.txt`，并在 Vue 与 C/B 演示目录运行 `npm ci`。不会安装到全局 Python。若 PowerShell 执行策略阻止脚本，可对单次调用使用 `powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1`。

## 启动/停止

```powershell
.\scripts\start.ps1
.\scripts\stop.ps1
```

启动前检查 8000、5173、5174 三个端口；后台窗口隐藏，日志和 PID 写入 `.runtime/`。三项服务健康检查通过后报告启动成功，失败时清理本次服务。

| 服务 | 地址 | 代码目录 |
| --- | --- | --- |
| 医生与管理员 | http://127.0.0.1:5173/login | admin-web |
| 正式患者入口 | http://127.0.0.1:5173/p/fill/demo-patient-token | admin-web |
| 独立 C/B Mock 演示 | http://127.0.0.1:5174/ | patient-web/c2b/Frontend |
| API / Swagger | http://127.0.0.1:8000/docs | server |

演示医生 `doctor1 / Doctor123!`，管理员 `admin / Admin123!`，演示患者访问码 `123456`。真实新派发任务使用返回的链接及对应 6 位码。

手机与电脑处于同一局域网时，使用启动脚本打印的 LAN 地址。API 经 5173 的 Vite 代理转发。虚拟网卡或多个网卡可能导致自动选择的地址不可达；可直接在 PowerShell 设置 `FRONTEND_ORIGIN` 后手动启动后端，前端使用 `--host 0.0.0.0`。

## 数据与环境变量

配置通过**进程环境变量**读取；根目录 `.env.example` 是变量清单，复制为 `.env` 不会自动加载。

```powershell
$env:DATABASE_URL = 'sqlite:///D:/data/cyb-demo.db'
$env:JWT_SECRET = 'local-demo-change-this-secret'
```

未设置 `DATABASE_URL` 时使用 `%TEMP%/ad_questionnaire_cyb_<工作区路径哈希>/ad_questionnaire.db`，避免不同分支共享数据库，也规避当前 Windows SQLite 中文路径问题。数据库在服务启动时初始化并执行 Alembic 兼容迁移，重启保留数据。指定已有数据库前自行保留备份；自动测试使用独立临时数据库。

启动脚本为本次后端设置 LAN `FRONTEND_ORIGIN`，启动后恢复父进程原值。要手动控制：

```powershell
$env:FRONTEND_ORIGIN = 'http://127.0.0.1:5173'
# 终端一
Push-Location server
..\.venv\Scripts\python.exe run.py
Pop-Location
# 终端二
npm run dev --prefix admin-web -- --host 0.0.0.0
# 终端三
npm run dev --prefix patient-web/c2b/Frontend -- --host 0.0.0.0
```

## 验证

```powershell
.\scripts\test.ps1
# 三个服务启动后运行浏览器测试（会添加编号化虚拟测试患者/任务）
Push-Location admin-web
npx playwright install chromium
npm run test:e2e
Pop-Location
```

后端测试、Vue 构建、C/B 类型检查/测试/构建通过才算脚本成功。浏览器测试覆盖手机填写/草稿恢复/历史、切换链接验证、离开保存、医生主要页面和四项 C/B 入口。截图保存在 `admin-web/test-results/`，不提交运行数据或构建产物。

出现问题先查看 `.runtime/backend-error.log`、`frontend-error.log` 和 `demo-error.log`。端口被其他程序占用时不会强制结束其他程序。

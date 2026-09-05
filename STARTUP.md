# 启动说明

## 环境要求

- Node.js 20
- npm 10 或兼容版本
- 建议在 WSL 或 Linux 环境中运行

如果当前环境使用 `nvm`，先执行：

```bash
export NVM_DIR="/home/lfy/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"
nvm use 20
```

## 安装依赖

```bash
npm install
```

## 启动开发服务器

先在第一个终端启动答题后端：

```bash
npm run dev:server
```

再在第二个终端启动患者前端：

```bash
npm run dev
```

默认情况下，Vite 会输出本地访问地址，例如：

```text
http://localhost:5173/
```

如果端口被占用，可指定端口：

```bash
npm run dev -- --port 4173
```

## 生产构建

```bash
npm run build
```

## MVP 测试路径

1. 打开 `/login`
2. 进入“管理员模式”
3. 在 `/admin` 为演示患者派发 `SCD-Q9`
4. 进入 `/home`
5. 打开 `SCD-Q9`
6. 逐题作答并提交
7. 在完成页查看结构化提交结果

## 数据说明

- 任务、草稿和提交通过 `/api` 保存到 `server/data/store.json`
- 前端开发服务器会把 `/api` 代理到 `http://127.0.0.1:3001`
- `server/data/store.json` 是本地运行数据，已加入 `.gitignore`
- 管理员页面的“重置全部演示数据”会清空任务、草稿和提交

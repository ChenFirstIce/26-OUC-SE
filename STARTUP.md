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

- 运行中的任务、草稿和提交都保存在浏览器 `localStorage`
- 清空浏览器站点数据后，演示数据会被重置

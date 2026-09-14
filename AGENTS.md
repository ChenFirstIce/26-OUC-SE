# cyb 集成工作约定

- 用户已明确授权从 main 创建 cyb，并按功能整合 main、yjj、dl、lfy。
- 在 cyb 工作区维护集成结果；不修改其他分支或原工作区的未提交内容。
- README.md 是目录和启动入口；启动变化同步 STARTUP.md，API 变化同步 contracts/API.md。
- 源分支固定版本与文件去向记录在 docs/integration/；覆盖评估区分真实后端、演示和缺口。
- server/app/main.py 只注册 routers/；modules/ 为历史草案，不接入正式流程。
- 完成相关测试后再报告成功；不提交依赖、构建输出、运行数据库或真实患者数据。

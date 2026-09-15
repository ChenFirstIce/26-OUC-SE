@echo off
REM SCD 和 STT 集成验证脚本（Windows 版本）
REM 用于快速验证系统集成状态

echo ==================================================
echo   SCD + STT 量表系统集成验证
echo ==================================================
echo.

echo 1. 检查数据文件
echo -----------------------------------
if exist scd_structured_interview.json (
    echo [32m✓[0m 找到: scd_structured_interview.json
) else (
    echo [31m✗[0m 缺失: scd_structured_interview.json
)
if exist stt_age_thresholds.json (
    echo [32m✓[0m 找到: stt_age_thresholds.json
) else (
    echo [31m✗[0m 缺失: stt_age_thresholds.json
)
if exist stt_sequences_with_coordinates.json (
    echo [32m✓[0m 找到: stt_sequences_with_coordinates.json
) else (
    echo [31m✗[0m 缺失: stt_sequences_with_coordinates.json
)
echo.

echo 2. 检查后端文件
echo -----------------------------------
if exist server\app\seed.py (
    echo [32m✓[0m 找到: server\app\seed.py
) else (
    echo [31m✗[0m 缺失: server\app\seed.py
)
if exist server\app\routers\assisted_tasks.py (
    echo [32m✓[0m 找到: server\app\routers\assisted_tasks.py
) else (
    echo [31m✗[0m 缺失: server\app\routers\assisted_tasks.py
)
if exist server\app\services\stt_scale.py (
    echo [32m✓[0m 找到: server\app\services\stt_scale.py
) else (
    echo [31m✗[0m 缺失: server\app\services\stt_scale.py
)
echo.

echo 3. 检查前端组件
echo -----------------------------------
if exist admin-web\src\components\questionnaire\ScdQuestionnaire.vue (
    echo [32m✓[0m 找到: ScdQuestionnaire.vue
) else (
    echo [31m✗[0m 缺失: ScdQuestionnaire.vue
)
if exist admin-web\src\data\scd-questionnaire.ts (
    echo [32m✓[0m 找到: scd-questionnaire.ts
) else (
    echo [31m✗[0m 缺失: scd-questionnaire.ts
)
if exist admin-web\src\components\patient\AssistedTask.vue (
    echo [32m✓[0m 找到: AssistedTask.vue
) else (
    echo [31m✗[0m 缺失: AssistedTask.vue
)
if exist admin-web\src\components\ReviewEvidence.vue (
    echo [32m✓[0m 找到: ReviewEvidence.vue
) else (
    echo [31m✗[0m 缺失: ReviewEvidence.vue
)
echo.

echo 4. 检查文档
echo -----------------------------------
if exist README.md (
    echo [32m✓[0m 找到: README.md
) else (
    echo [31m✗[0m 缺失: README.md
)
if exist INTEGRATION_COMPLETE.md (
    echo [32m✓[0m 找到: INTEGRATION_COMPLETE.md
) else (
    echo [31m✗[0m 缺失: INTEGRATION_COMPLETE.md
)
if exist QUICKSTART.md (
    echo [32m✓[0m 找到: QUICKSTART.md
) else (
    echo [31m✗[0m 缺失: QUICKSTART.md
)
if exist CHANGELOG.md (
    echo [32m✓[0m 找到: CHANGELOG.md
) else (
    echo [31m✗[0m 缺失: CHANGELOG.md
)
echo.

echo 5. 前端构建测试
echo -----------------------------------
cd admin-web
call npm run build >/dev/null 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [32m✓[0m 前端构建成功
) else (
    echo [31m✗[0m 前端构建失败
)
cd ..
echo.

echo ==================================================
echo   验证完成
echo ==================================================
echo.
echo 下一步操作：
echo   1. 启动后端: cd server ^&^& python -m uvicorn app.main:app --reload
echo   2. 启动前端: cd admin-web ^&^& npm run dev
echo   3. 访问系统: http://localhost:5173
echo   4. 参考文档: QUICKSTART.md
echo.
echo ==================================================
pause

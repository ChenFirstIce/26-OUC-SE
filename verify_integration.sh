#!/bin/bash

# SCD 和 STT 集成验证脚本
# 用于快速验证系统集成状态

echo "=================================================="
echo "  SCD + STT 量表系统集成验证"
echo "=================================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查函数
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} 找到: $1"
        return 0
    else
        echo -e "${RED}✗${NC} 缺失: $1"
        return 1
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} 目录存在: $1"
        return 0
    else
        echo -e "${RED}✗${NC} 目录缺失: $1"
        return 1
    fi
}

echo "1. 检查数据文件"
echo "-----------------------------------"
check_file "scd_structured_interview.json"
check_file "stt_age_thresholds.json"
check_file "stt_sequences_with_coordinates.json"
echo ""

echo "2. 检查后端文件"
echo "-----------------------------------"
check_file "server/app/seed.py"
check_file "server/app/routers/assisted_tasks.py"
check_file "server/app/services/stt_scale.py"
echo ""

echo "3. 检查前端组件"
echo "-----------------------------------"
check_file "admin-web/src/components/questionnaire/ScdQuestionnaire.vue"
check_file "admin-web/src/data/scd-questionnaire.ts"
check_file "admin-web/src/components/patient/AssistedTask.vue"
check_file "admin-web/src/components/ReviewEvidence.vue"
echo ""

echo "4. 检查文档"
echo "-----------------------------------"
check_file "README.md"
check_file "INTEGRATION_COMPLETE.md"
check_file "QUICKSTART.md"
check_file "CHANGELOG.md"
echo ""

echo "5. 前端构建测试"
echo "-----------------------------------"
cd admin-web
if npm run build > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} 前端构建成功"
    BUILD_SUCCESS=true
else
    echo -e "${RED}✗${NC} 前端构建失败"
    BUILD_SUCCESS=false
fi
cd ..
echo ""

echo "6. 后端模块导入测试"
echo "-----------------------------------"
cd server
if python -c "from app.seed import CB_DEMOS; from app.services.stt_scale import STT_AGE_BANDS" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} 后端模块导入成功"
    IMPORT_SUCCESS=true
else
    echo -e "${YELLOW}⚠${NC} 后端模块导入需要安装依赖"
    IMPORT_SUCCESS=false
fi
cd ..
echo ""

echo "=================================================="
echo "  验证总结"
echo "=================================================="

if $BUILD_SUCCESS; then
    echo -e "${GREEN}✓ 前端集成完成${NC}"
else
    echo -e "${RED}✗ 前端集成存在问题${NC}"
fi

if $IMPORT_SUCCESS; then
    echo -e "${GREEN}✓ 后端集成完成${NC}"
else
    echo -e "${YELLOW}⚠ 后端需要安装依赖: pip install -r server/requirements.txt${NC}"
fi

echo ""
echo "下一步操作："
echo "  1. 启动后端: cd server && uvicorn app.main:app --reload"
echo "  2. 启动前端: cd admin-web && npm run dev"
echo "  3. 访问系统: http://localhost:5173"
echo "  4. 参考文档: QUICKSTART.md"
echo ""
echo "=================================================="

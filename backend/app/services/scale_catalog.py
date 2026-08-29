from copy import deepcopy


SOURCE_ROOT = "https://gitee.com/oucwy/ad-ouc/raw/master"


def option(value, label, score=0):
    return {"value": value, "label": label, "score": score}


YN = [option("yes", "是", 1), option("no", "否", 0)]
FREQUENCY = [option("often", "经常", 1), option("sometimes", "偶尔", 0.5), option("never", "从未", 0)]


def source(file_name: str, mode: str, note: str) -> dict:
    return {
        "repository": "oucwy/ad-ouc", "file_name": file_name,
        "url": f"{SOURCE_ROOT}/{file_name}", "administration_mode": mode,
        "license_status": "institution_review_required", "review_note": note,
    }


def numeric_question(key: str, label: str, maximum: int, dimension: str):
    return {"key": key, "type": "integer", "label": label, "required": True,
            "min": 0, "max": maximum, "score_numeric": True, "dimension": dimension}


SCALE_CATALOG = [
    {
        "code": "OUC_SCD_Q9", "name": "主观认知下降自测表（SCD-Q9）",
        "description": "来自仓库综合 SCD 筛查 PDF 的 9 题结构化自评版。",
        "questionnaire_schema": {
            "title": "主观认知下降自测表（SCD-Q9）", "administration_mode": "patient_self",
            "notice": "请根据近期真实情况作答。结果仅供专业人员综合评估。",
            "source": source("1_AD临床前期SCD筛查量表-基线期-加上情景选择题.pdf", "patient_self", "题目可文本提取；正式使用前仍需机构确认授权及评分解释。"),
            "sections": [{"key": "scd_q9", "title": "记忆与认知变化", "questions": [
                {"key": "scd_1", "type": "yes_no", "label": "你认为自己有记忆问题吗？", "required": True, "options": YN, "dimension": "主观认知"},
                {"key": "scd_2", "type": "yes_no", "label": "你回忆 3-5 天前的对话有困难吗？", "required": True, "options": YN, "dimension": "主观认知"},
                {"key": "scd_3", "type": "yes_no", "label": "你觉得自己近两年有记忆问题吗？", "required": True, "options": YN, "dimension": "主观认知"},
                {"key": "scd_4", "type": "single_choice", "label": "忘记对个人来说重要的日期（如生日等）的情况经常发生吗？", "required": True, "options": FREQUENCY, "dimension": "日常记忆"},
                {"key": "scd_5", "type": "single_choice", "label": "忘记常用号码的情况经常发生吗？", "required": True, "options": FREQUENCY, "dimension": "日常记忆"},
                {"key": "scd_6", "type": "yes_no", "label": "总的来说，你是否认为自己对要做的事或要说的话容易忘记？", "required": True, "options": YN, "dimension": "日常记忆"},
                {"key": "scd_7", "type": "single_choice", "label": "到了商店忘记要买什么的情况经常发生吗？", "required": True, "options": FREQUENCY, "dimension": "日常记忆"},
                {"key": "scd_8", "type": "yes_no", "label": "你认为自己的记忆力比 5 年前要差吗？", "required": True, "options": YN, "dimension": "主观认知"},
                {"key": "scd_9", "type": "yes_no", "label": "你认为自己越来越记不住东西放在哪里了吗？", "required": True, "options": YN, "dimension": "日常记忆"},
            ]}],
        },
        "scoring_json": {"strategy": "metadata_sum", "risk_thresholds": []},
    },
    {
        "code": "OUC_MMSE", "name": "简明精神状态检查（MMSE）- 分域录入版",
        "description": "供受训医务人员录入各分域得分，保留总分和分域结果。",
        "questionnaire_schema": {
            "title": "MMSE 分域得分录入", "administration_mode": "clinician",
            "notice": "本量表应由受训人员施测；此模板用于结构化记录，不代替操作手册。",
            "source": source("1_AD临床前期SCD筛查量表-基线期-加上情景选择题.pdf", "clinician", "综合 PDF 中含完整 MMSE 操作题目；本系统导入分域录入版。"),
            "sections": [{"key": "scores", "title": "分域得分", "questions": [
                numeric_question("orientation", "定向力得分", 10, "定向力"), numeric_question("registration", "即刻记忆得分", 3, "即刻记忆"),
                numeric_question("attention", "注意与计算得分", 5, "注意与计算"), numeric_question("recall", "延迟回忆得分", 3, "延迟回忆"),
                numeric_question("language", "语言与执行得分", 9, "语言与执行"),
            ]}],
        }, "scoring_json": {"strategy": "metadata_sum", "risk_thresholds": []},
    },
    {
        "code": "OUC_FAQ", "name": "功能活动问卷（FAQ）",
        "description": "10 项日常功能活动结构化记录版。",
        "questionnaire_schema": {
            "title": "功能活动问卷（FAQ）", "administration_mode": "informant",
            "notice": "建议由熟悉患者日常生活的知情者协助完成。",
            "source": source("1_AD临床前期SCD筛查量表-基线期-加上情景选择题.pdf", "informant", "题目可文本提取；正式使用前需确认授权及 NA 处理规则。"),
            "sections": [{"key": "faq", "title": "日常功能", "questions": [
                {"key": f"faq_{index}", "type": "scale", "label": label, "required": True, "dimension": "日常功能",
                 "options": [option(0, "0 - 独立完成", 0), option(1, "1 - 需要指导或监督", 1), option(2, "2 - 需要帮助", 2), option(3, "3 - 无法完成", 3), option("NA", "不适用", 0)]}
                for index, label in enumerate([
                    "使用电话或手机", "整理家庭物品", "自行购物", "参加需要技巧的活动", "使用各种电器",
                    "准备和烹饪一顿饭菜", "关心和了解新鲜事物", "持续专注看电视、阅读或收听节目",
                    "记得重要时间点", "独自外出活动或走亲访友",
                ], 1)
            ]}],
        }, "scoring_json": {"strategy": "metadata_sum", "risk_thresholds": []},
    },
    {
        "code": "OUC_MOCA_B", "name": "蒙特利尔认知评估基础版（MoCA-B）- 结果录入版",
        "description": "支持记录 MoCA-B 总分、教育校正和施测备注；原 PDF 含视觉题，需按授权手册施测。",
        "questionnaire_schema": {
            "title": "MoCA-B 结果录入", "administration_mode": "clinician",
            "notice": "原量表含图形任务，应由具备相应资质的人员按正式材料施测。",
            "source": source("3.量表MoCA模板.pdf", "clinician", "扫描图像型 PDF；系统仅提供结果录入，不复制视觉题。"),
            "sections": [{"key": "result", "title": "施测结果", "questions": [
                numeric_question("moca_total", "校正前总分", 30, "MoCA-B"),
                {"key": "education_years", "type": "integer", "label": "受教育年限", "required": False, "min": 0, "max": 30},
                {"key": "education_correction", "type": "yes_no", "label": "是否按授权手册进行了教育校正？", "required": True, "options": [option("yes", "是"), option("no", "否")]},
                {"key": "examiner_note", "type": "long_text", "label": "施测备注", "required": False},
            ]}],
        }, "scoring_json": {"strategy": "metadata_sum", "risk_thresholds": []},
    },
    {
        "code": "OUC_CDR", "name": "临床痴呆评定量表（CDR）- 分域录入版",
        "description": "支持六个 CDR 分域和全局 CDR 结果的结构化记录。",
        "questionnaire_schema": {
            "title": "CDR 分域结果录入", "administration_mode": "clinician",
            "notice": "CDR 需要分别访谈知情者和受试者，并由专业人员综合判定。",
            "source": source("5.CDR.pdf", "clinician", "文本型 PDF；全局 CDR 不能用简单加总代替专业判定。"),
            "sections": [{"key": "domains", "title": "分域评级", "questions": [
                {"key": key, "type": "scale", "label": label, "required": True, "dimension": label,
                 "options": [option(0, "0"), option(0.5, "0.5"), option(1, "1"), option(2, "2"), option(3, "3")]}
                for key, label in [("memory", "记忆"), ("orientation", "定向"), ("judgment", "判断和解决问题"),
                                   ("community", "社会事务"), ("home", "家庭与爱好"), ("care", "个人照料")]
            ] + [{"key": "global_cdr", "type": "scale", "label": "全局 CDR", "required": True,
                  "options": [option(0, "0"), option(0.5, "0.5"), option(1, "1"), option(2, "2"), option(3, "3")]}]}],
        }, "scoring_json": {"strategy": "manual_review"},
    },
    {
        "code": "OUC_ADAS_COG", "name": "ADAS-Cog - 结果录入版",
        "description": "支持记录 ADAS-Cog 总分及施测说明；原文件含图形与操作任务。",
        "questionnaire_schema": {
            "title": "ADAS-Cog 结果录入", "administration_mode": "clinician",
            "notice": "应由受训人员使用正式授权材料施测，本模板用于保存结果。",
            "source": source("6.ADAS-cog.pdf", "clinician", "PDF 含图像和操作任务；系统不自动重建受版权约束的视觉材料。"),
            "sections": [{"key": "result", "title": "施测结果", "questions": [
                numeric_question("adas_total", "ADAS-Cog 总分", 100, "ADAS-Cog"),
                {"key": "version", "type": "short_text", "label": "量表版本", "required": False},
                {"key": "examiner_note", "type": "long_text", "label": "施测备注", "required": False},
            ]}],
        }, "scoring_json": {"strategy": "metadata_sum", "risk_thresholds": []},
    },
]


def catalog_items() -> list[dict]:
    return deepcopy(SCALE_CATALOG)

import os

INDEX_PATH = r"C:\Users\RM\.gemini\antigravity\scratch\worksite_bookkeeping_app\templates\index.html"

with open(INDEX_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Simplify text strings
replacements = {
    "分账过滤查看方式:": "账单视图:",
    "全部卸土点总览": "全盘汇总",
    "车辆出运汇总一览(卡片一览)": "车辆账单",
    "车辆出运汇总一览": "车辆账单",
    "今日记账明细流水": "今日流水",
    "记账明细流水": "今日流水",
    "每日对账分账明细一览": "对账单明细",
    "卸土点/分账去向名称": "卸土点",
    "消纳去向 (卸土点)": "卸土点",
    "拉运土方类型": "土方类型",
    "分账单价 (元/趟)": "单价(元)",
    "对账结算总金额": "总额(元)",
    "待指派审计趟数": "待分账(趟)",
    "账目审计微调": "操作",
    "出场运输趟数": "总趟数",
    "对账净结算金额": "净收支",
    "对账对齐微调": "操作",
    "快捷审计分账": "去分账",
    "对账审计 / 微调": "账目明细",
}

for old, new in replacements.items():
    content = content.replace(old, new)
    
# Make sure the JS logic matches the new strings
# In JS, activeSiteFilter checks:
content = content.replace('!["今日流水", "全盘汇总", "车辆账单"].includes(activeSiteFilter)', '!["今日流水", "全盘汇总", "车辆账单"].includes(activeSiteFilter)')
content = content.replace('activeSiteFilter === "今日流水"', 'activeSiteFilter === "今日流水"')
content = content.replace('activeSiteFilter === "全盘汇总"', 'activeSiteFilter === "全盘汇总"')
content = content.replace('activeSiteFilter === "车辆账单"', 'activeSiteFilter === "车辆账单"')

# 2. CSS Revamp to Premium Sleek Dark Mode
new_css_vars = """
        :root {
            color-scheme: dark;
            --bg-color: #0b0f19;
            --header-bg: rgba(15, 23, 42, 0.7);
            --card-bg: rgba(30, 41, 59, 0.7);
            --card-hover-bg: rgba(30, 41, 59, 0.9);
            --card-border: rgba(51, 65, 85, 0.6);
            --card-border-hover: rgba(99, 102, 241, 0.5);
            
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            
            --color-primary: #6366f1;
            --color-primary-hover: #818cf8;
            --color-primary-active-bg: rgba(99, 102, 241, 0.15);
            --color-primary-active-border: rgba(99, 102, 241, 0.3);
            --color-primary-hover-bg: rgba(99, 102, 241, 0.1);
            --color-primary-active-shadow: rgba(99, 102, 241, 0.4);
            
            --color-in: #34d399;
            --color-in-light: rgba(52, 211, 153, 0.15);
            
            --color-out: #38bdf8;
            --color-out-light: rgba(56, 189, 248, 0.15);
            
            --color-stay: #fbbf24;
            --color-stay-light: rgba(251, 191, 36, 0.15);
            
            --color-danger: #f87171;
            --color-danger-light: rgba(248, 113, 113, 0.15);

            --bg-image: radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.15) 0px, transparent 50%),
                        radial-gradient(at 100% 100%, rgba(56, 189, 248, 0.1) 0px, transparent 50%),
                        radial-gradient(at 50% 50%, #0b0f19 0px, #0f172a 100%);
            
            --kpi-bg: rgba(30, 41, 59, 0.6);
            --kpi-hover-bg: rgba(30, 41, 59, 0.95);
            --kpi-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            
            --sub-panel-bg: rgba(15, 23, 42, 0.5);
            --input-bg: rgba(15, 23, 42, 0.8);
            --input-focus-shadow: rgba(99, 102, 241, 0.4);
            
            --btn-sec-bg: rgba(51, 65, 85, 0.5);
            --btn-sec-border: rgba(71, 85, 105, 0.8);
            --btn-sec-color: #cbd5e1;
            --btn-sec-hover-bg: rgba(71, 85, 105, 0.8);
            --btn-sec-hover-border: #94a3b8;
            --btn-sec-hover-color: #f1f5f9;
            
            --suggestions-bg: #1e293b;
            --suggestions-border: #334155;
            --suggestions-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
            --suggestions-hover-bg: #334155;
            
            --rank-badge-bg: rgba(51, 65, 85, 0.5);
            --rank-trips-bg: rgba(56, 189, 248, 0.1);
            --rank-trips-border: rgba(56, 189, 248, 0.3);
            --rank-trips-color: #38bdf8;
            
            --filter-bar-bg: rgba(30, 41, 59, 0.5);
            --table-bg: transparent;
            --table-th-bg: rgba(15, 23, 42, 0.6);
            --table-border: rgba(51, 65, 85, 0.6);
            --table-hover-bg: rgba(51, 65, 85, 0.4);
            
            --summary-bar-bg: rgba(16, 185, 129, 0.1);
            --summary-bar-border: rgba(16, 185, 129, 0.3);
            
            --card-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
            --card-hover-shadow: 0 12px 48px rgba(0, 0, 0, 0.4);
            
            --modal-bg: #1e293b;
            --modal-shadow: 0 25px 60px rgba(0, 0, 0, 0.6);
            --modal-overlay-bg: rgba(0, 0, 0, 0.6);
            
            --chart-grid-stroke: rgba(255, 255, 255, 0.05);
            --chart-bar-bg: rgba(51, 65, 85, 0.5);
            --chart-line-start: #818cf8;
            --chart-line-end: #38bdf8;
            --chart-area-start: rgba(129, 140, 248, 0.3);
            --chart-area-end: rgba(129, 140, 248, 0);
            --chart-node-fill: #818cf8;
            
            --font-family: 'Outfit', 'Noto Sans SC', system-ui, sans-serif;
            --border-radius-lg: 20px;
            --border-radius-md: 14px;
            --border-radius-sm: 8px;
"""

import re
content = re.sub(r':root\s*\{[^}]+\}', new_css_vars, content, count=1)

with open(INDEX_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("Simplified UI text and applied premium dark theme.")

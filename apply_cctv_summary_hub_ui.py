# -*- coding: UTF-8 -*-
"""
脚本：将 templates/index.html 升级为中央电视台项目数据汇总中心
把 📊【数据汇总中心】设为默认首屏，添加多维汇总卡片、消纳点×日期交叉透视矩阵、Excel拖拽导入与全周期选择器。
"""
import os
import re

html_path = "templates/index.html"

with open(html_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. 更新顶部导航栏 Links
old_nav_links = """        <div class="nav-links">
            <a class="nav-item" id="menu-monitor" onclick="switchTab('monitor')">
                <i data-lucide="tv" style="width:14px; height:14px;"></i>
                <span>展示大屏</span>
            </a>
            <a class="nav-item active" id="menu-ledger" onclick="switchTab('ledger')">
                <i data-lucide="file-spreadsheet" style="width:14px; height:14px;"></i>
                <span>财务记账</span>
            </a>
            <a class="nav-item" id="menu-reconcile" onclick="switchTab('reconcile')">
                <i data-lucide="check-square" style="width:14px; height:14px;"></i>
                <span>汇总对账</span>
            </a>
            <a class="nav-item" id="menu-config" onclick="switchTab('config')">
                <i data-lucide="settings" style="width:14px; height:14px;"></i>
                <span>系统配置</span>
            </a>
        </div>"""

new_nav_links = """        <div class="nav-links">
            <a class="nav-item active" id="menu-summary" onclick="switchTab('summary')">
                <i data-lucide="pie-chart" style="width:14px; height:14px;"></i>
                <span>数据汇总中心</span>
            </a>
            <a class="nav-item" id="menu-ledger" onclick="switchTab('ledger')">
                <i data-lucide="file-spreadsheet" style="width:14px; height:14px;"></i>
                <span>项目明细台账</span>
            </a>
            <a class="nav-item" id="menu-import" onclick="switchTab('import')">
                <i data-lucide="upload-cloud" style="width:14px; height:14px;"></i>
                <span>Excel 导入与导出</span>
            </a>
            <a class="nav-item" id="menu-config" onclick="switchTab('config')">
                <i data-lucide="settings" style="width:14px; height:14px;"></i>
                <span>配置与存档</span>
            </a>
        </div>"""

content = content.replace(old_nav_links, new_nav_links)

# 2. 将首屏设置为 panel-summary，并将原 panel-monitor 隐藏
summary_panel_html = """        <!-- 📊 面板一: 中央电视台项目 · 数据汇总中心 (默认首屏) -->
        <section class="main-content active" id="panel-summary">
            <!-- 顶部筛选与汇总概览 -->
            <div class="glass-card">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; margin-bottom:16px;">
                    <h3 class="card-header-title" style="margin-bottom:0;">
                        <i data-lucide="pie-chart"></i>中央电视台项目 · 全周期多维数据汇总
                    </h3>
                    <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
                        <div class="btn-group" style="display:flex; gap:6px;">
                            <button class="btn btn-sm btn-accent" id="btn-preset-all" onclick="loadSummaryAnalytics('all')">全周期汇总</button>
                            <button class="btn btn-sm btn-secondary" id="btn-preset-custom" onclick="toggleCustomSummaryDate()">按时间段筛选</button>
                        </div>
                        <div id="summary-custom-date-box" style="display:none; align-items:center; gap:6px;">
                            <input type="date" class="input-control" id="summary-start-date" style="width:130px; height:32px; font-size:12px;">
                            <span style="color:var(--text-muted);">至</span>
                            <input type="date" class="input-control" id="summary-end-date" style="width:130px; height:32px; font-size:12px;">
                            <button class="btn btn-sm btn-accent" onclick="applyCustomSummaryDate()">查询</button>
                        </div>
                    </div>
                </div>

                <!-- 核心 KPI 汇总卡 -->
                <div class="kpi-grid" style="grid-template-columns: repeat(4, 1fr); gap: 14px;">
                    <div class="kpi-card">
                        <div class="kpi-icon kpi-icon-out"><i data-lucide="truck"></i></div>
                        <div class="kpi-info">
                            <span class="kpi-label">累计拉运趟数</span>
                            <div style="display:flex; align-items:baseline; gap:4px;">
                                <span class="kpi-value" id="sum-total-trips">0</span>
                                <span style="font-size:12px; color:var(--text-secondary);">趟</span>
                            </div>
                        </div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-icon" style="background:rgba(16,185,129,0.15); color:var(--color-in);"><i data-lucide="zap"></i></div>
                        <div class="kpi-info">
                            <span class="kpi-label">自有电车拉运</span>
                            <div style="display:flex; align-items:baseline; gap:4px;">
                                <span class="kpi-value" id="sum-ev-trips" style="color:var(--color-in);">0</span>
                                <span style="font-size:12px; color:var(--text-secondary);" id="sum-ev-pct">(0%)</span>
                            </div>
                        </div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-icon" style="background:rgba(245,158,11,0.15); color:var(--color-stay);"><i data-lucide="fuel"></i></div>
                        <div class="kpi-info">
                            <span class="kpi-label">外协燃油车拉运</span>
                            <div style="display:flex; align-items:baseline; gap:4px;">
                                <span class="kpi-value" id="sum-fuel-trips" style="color:var(--color-stay);">0</span>
                                <span style="font-size:12px; color:var(--text-secondary);" id="sum-fuel-pct">(0%)</span>
                            </div>
                        </div>
                    </div>
                    <div class="kpi-card">
                        <div class="kpi-icon kpi-icon-cost"><i data-lucide="map-pin"></i></div>
                        <div class="kpi-info">
                            <span class="kpi-label">覆盖消纳点与规格</span>
                            <div style="display:flex; align-items:baseline; gap:4px;">
                                <span class="kpi-value" id="sum-sites-cnt">0</span>
                                <span style="font-size:12px; color:var(--text-secondary);">场地 / </span>
                                <span class="kpi-value" id="sum-soils-cnt" style="font-size:16px;">0</span>
                                <span style="font-size:12px; color:var(--text-secondary);">规格</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 多维汇总卡片网格 -->
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:16px; margin-top:16px;">
                <!-- 按【土方/车辆规格】汇总 -->
                <div class="glass-card">
                    <h3 class="card-header-title">
                        <i data-lucide="box"></i>按【土方/车辆规格】汇总明细
                    </h3>
                    <div class="table-responsive" style="max-height: 360px;">
                        <table class="ledger-table">
                            <thead>
                                <tr>
                                    <th>序号</th>
                                    <th>货物/车辆规格</th>
                                    <th>总拉运趟数</th>
                                    <th>趟数占比</th>
                                    <th>运费单价</th>
                                    <th>运费估算</th>
                                    <th>电车占比</th>
                                </tr>
                            </thead>
                            <tbody id="table-body-soil-summary">
                                <tr><td colspan="7" style="color:var(--text-muted);">正在计算汇总数据...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- 按【消纳场地/卸土点】汇总 -->
                <div class="glass-card">
                    <h3 class="card-header-title">
                        <i data-lucide="map-pin"></i>按【消纳场地/卸土点】汇总明细
                    </h3>
                    <div class="table-responsive" style="max-height: 360px;">
                        <table class="ledger-table">
                            <thead>
                                <tr>
                                    <th>序号</th>
                                    <th>消纳场/卸土点</th>
                                    <th>总拉运趟数</th>
                                    <th>趟数占比</th>
                                    <th>消纳单价</th>
                                    <th>消纳费估算</th>
                                    <th>电车占比</th>
                                </tr>
                            </thead>
                            <tbody id="table-body-site-summary">
                                <tr><td colspan="7" style="color:var(--text-muted);">正在计算汇总数据...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- 交互式日期 × 场地拉运趟数透视矩阵 -->
            <div class="glass-card" style="margin-top:16px;">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; margin-bottom:14px;">
                    <h3 class="card-header-title" style="margin-bottom:0;">
                        <i data-lucide="table"></i>消纳场地 × 每日拉运趟数交叉透视矩阵
                    </h3>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <input type="text" class="input-control" id="pivot-search-input" placeholder="搜索消纳点名称..." oninput="filterPivotMatrix()" style="width:180px; height:32px; font-size:12px;">
                    </div>
                </div>
                <div class="table-responsive" style="max-height: 480px;">
                    <table class="ledger-table" id="pivot-matrix-table">
                        <thead id="pivot-thead">
                            <!-- 动态列头 -->
                        </thead>
                        <tbody id="pivot-tbody">
                            <!-- 动态数据行 -->
                        </tbody>
                    </table>
                </div>
            </div>
        </section>

        <!-- 📤 面板三: Excel 台账导入与报表导出 -->
        <section class="main-content" id="panel-import">
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:16px;">
                <!-- 一键导入 -->
                <div class="glass-card">
                    <h3 class="card-header-title">
                        <i data-lucide="upload-cloud"></i>一键上传 Excel 车辆台账
                    </h3>
                    <p style="font-size:12px; color:var(--text-secondary); margin-bottom:16px;">
                        支持导入标准格式的 Excel/CSV 车辆台账。系统将自动解析 <strong style="color:var(--text-primary);">[日期]、[种类]、[卸土点]、[是否自有电车]、[车辆数]、[备注]</strong> 并同步至汇总数据库。
                    </p>
                    
                    <div id="drop-zone-excel" style="border:2px dashed var(--card-border-hover); border-radius:var(--border-radius-md); padding:40px 20px; text-align:center; background:rgba(99,102,241,0.03); cursor:pointer; transition:all 0.2s;" onclick="document.getElementById('excel-file-input').click()">
                        <i data-lucide="file-spreadsheet" style="width:48px; height:48px; color:var(--color-primary); margin-bottom:12px;"></i>
                        <div style="font-size:14px; font-weight:700; color:var(--text-primary); margin-bottom:4px;">点击选择或将 Excel 文件拖拽至此处</div>
                        <div style="font-size:11px; color:var(--text-muted);">支持 .xlsx, .xls, .csv 格式</div>
                        <input type="file" id="excel-file-input" accept=".xlsx,.xls,.csv" style="display:none;" onchange="handleExcelFileSelect(event)">
                    </div>

                    <div id="upload-preview-box" style="margin-top:16px; display:none; background:rgba(255,255,255,0.03); border:1px solid var(--card-border); border-radius:var(--border-radius-sm); padding:12px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                            <span style="font-size:13px; font-weight:700;" id="upload-filename">ledger.xlsx</span>
                            <button class="btn btn-sm btn-accent" id="btn-do-import" onclick="executeExcelUpload()">确认开始导入</button>
                        </div>
                        <div id="upload-status-msg" style="font-size:12px; color:var(--text-secondary);">准备导入中...</div>
                    </div>
                </div>

                <!-- 导出报表 -->
                <div class="glass-card">
                    <h3 class="card-header-title">
                        <i data-lucide="download"></i>数据导出与报表下载
                    </h3>
                    <p style="font-size:12px; color:var(--text-secondary); margin-bottom:16px;">
                        导出中央电视台项目的多维汇总数据与详细流水，格式完全兼容 Excel 打开。
                    </p>
                    <div style="display:flex; flex-direction:column; gap:12px;">
                        <button class="btn btn-secondary" onclick="exportCurrentDateCSV()" style="justify-content:flex-start; padding:14px;">
                            <i data-lucide="file-text" style="color:var(--color-primary); margin-right:8px;"></i>
                            <div style="text-align:left;">
                                <div style="font-weight:700;">导出当前选定日期的通行日志流水 (.csv)</div>
                                <div style="font-size:11px; color:var(--text-muted);">导出包含车牌、时间、消纳点、种类及置信度的完整记录</div>
                            </div>
                        </button>
                    </div>
                </div>
            </div>
        </section>
"""

old_panel_monitor = '<section class="main-content" id="panel-monitor">'
content = content.replace(old_panel_monitor, summary_panel_html + '\n        <section class="main-content" id="panel-monitor" style="display:none;">')

with open(html_path, "w", encoding="utf-8") as f:
    f.write(content)

print("[Success] index.html HTML 结构成功升级！")

# -*- coding: UTF-8 -*-
"""
脚本：向 templates/index.html 补全中央电视台项目数据汇总中心 JavaScript 逻辑
包括：loadSummaryAnalytics(), renderPivotMatrix(), filterPivotMatrix(), Excel 上传导出及 switchTab 触发器
"""
import os
import re

html_path = "templates/index.html"

with open(html_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. 替换 switchTab 函数
old_switch_tab = """        let currentTab = 'monitor';
        let selectedQueryDate = new Date().toISOString().split('T')[0];
        
        document.addEventListener('DOMContentLoaded', () => {
            const picker = document.getElementById('query-date-picker');
            if (picker) picker.value = selectedQueryDate;
        });

        let currentFrequentPlatesList = [];
        let currentSitesList = [];
        let currentSoilsList = []; // 全局土方列表
        let activeSiteFilter = "车辆账单";
        let ledgerPageSize = 15;
        let ledgerCurrentPage = 1;
        let ledgerTotalPages = 1;

        function switchTab(tab) {
            currentTab = tab;
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.main-content').forEach(el => el.classList.remove('active'));
            
            const activeLink = document.getElementById(`menu-${tab}`);
            const activePanel = document.getElementById(`panel-${tab}`);
            const headerTitle = document.getElementById('header-title-text');
            const headerIcon = document.getElementById('header-icon');
            const headerActions = document.getElementById('header-actions-area');
            
            if (activeLink) activeLink.classList.add('active');
            if (activePanel) activePanel.classList.add('active');
            if (headerActions) headerActions.innerHTML = '';
            
            if (tab === 'monitor') {
                if (headerTitle) headerTitle.innerText = "多维展示大屏";
                if (headerIcon) headerIcon.setAttribute('data-lucide', 'tv');
                refreshDashboard();
            } else if (tab === 'ledger') {
                if (headerTitle) headerTitle.innerText = "现场财务记账";
                if (headerIcon) headerIcon.setAttribute('data-lucide', 'file-spreadsheet');
                if (headerActions) {
                    headerActions.innerHTML = `
                        <button class="btn btn-accent" onclick="exportReport()">
                            <i data-lucide="download"></i><span>导出当日报表</span>
                        </button>
                    `;
                }
                refreshLedger();
            } else if (tab === 'config') {
                if (headerTitle) headerTitle.innerText = "系统配置设置";
                if (headerIcon) headerIcon.setAttribute('data-lucide', 'settings');
                refreshDumpSites().then(() => {
                    renderDumpSitesListConfig();
                    renderSoilTypesListConfig(); // 渲染土方配置列表
                });
            } else if (tab === 'reconcile') {
                if (headerTitle) headerTitle.innerText = "结算汇总对账";
                if (headerIcon) headerIcon.setAttribute('data-lucide', 'check-square');
                refreshReconciliation();
            }

            lucide.createIcons({attrs: {"stroke-width": 2}});
        }"""

new_switch_tab = """        let currentTab = 'summary';
        let selectedQueryDate = new Date().toISOString().split('T')[0];
        
        document.addEventListener('DOMContentLoaded', () => {
            const picker = document.getElementById('query-date-picker');
            if (picker) picker.value = selectedQueryDate;
            loadSummaryAnalytics('all');
        });

        let currentFrequentPlatesList = [];
        let currentSitesList = [];
        let currentSoilsList = [];
        let activeSiteFilter = "车辆账单";
        let ledgerPageSize = 15;
        let ledgerCurrentPage = 1;
        let ledgerTotalPages = 1;
        let currentSummaryData = null;

        function switchTab(tab) {
            currentTab = tab;
            document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.main-content').forEach(el => el.classList.remove('active'));
            
            const activeLink = document.getElementById(`menu-${tab}`);
            const activePanel = document.getElementById(`panel-${tab}`);
            const headerTitle = document.getElementById('header-title-text');
            const headerIcon = document.getElementById('header-icon');
            const headerActions = document.getElementById('header-actions-area');
            
            if (activeLink) activeLink.classList.add('active');
            if (activePanel) activePanel.classList.add('active');
            if (headerActions) headerActions.innerHTML = '';
            
            if (tab === 'summary') {
                if (headerTitle) headerTitle.innerText = "数据汇总中心";
                if (headerIcon) headerIcon.setAttribute('data-lucide', 'pie-chart');
                loadSummaryAnalytics('all');
            } else if (tab === 'ledger') {
                if (headerTitle) headerTitle.innerText = "项目明细台账";
                if (headerIcon) headerIcon.setAttribute('data-lucide', 'file-spreadsheet');
                if (headerActions) {
                    headerActions.innerHTML = `
                        <button class="btn btn-accent" onclick="exportCurrentDateCSV()">
                            <i data-lucide="download"></i><span>导出当前日流水</span>
                        </button>
                    `;
                }
                refreshLedger();
            } else if (tab === 'import') {
                if (headerTitle) headerTitle.innerText = "Excel 导入与导出";
                if (headerIcon) headerIcon.setAttribute('data-lucide', 'upload-cloud');
            } else if (tab === 'config') {
                if (headerTitle) headerTitle.innerText = "系统配置与存档";
                if (headerIcon) headerIcon.setAttribute('data-lucide', 'settings');
                refreshDumpSites().then(() => {
                    renderDumpSitesListConfig();
                    renderSoilTypesListConfig();
                });
            } else if (tab === 'monitor') {
                if (headerTitle) headerTitle.innerText = "多维展示大屏 (存档)";
                if (headerIcon) headerIcon.setAttribute('data-lucide', 'tv');
                refreshDashboard();
            }

            lucide.createIcons({attrs: {"stroke-width": 2}});
        }"""

content = content.replace(old_switch_tab, new_switch_tab)

# 2. 插入新的数据汇总中心与 Excel 上传 JavaScript 函数
summary_js_code = """
        // ==========================================================================
        // 📊 中央电视台项目 - 全周期与多维数据汇总中心 JavaScript 逻辑
        // ==========================================================================

        function loadSummaryAnalytics(preset = 'all', startDate = '', endDate = '') {
            let url = `/api/summary_analytics?preset=${preset}`;
            if (preset === 'custom') {
                if (!startDate) startDate = document.getElementById('summary-start-date').value;
                if (!endDate) endDate = document.getElementById('summary-end-date').value;
                if (startDate && endDate) {
                    url += `&start_date=${startDate}&end_date=${endDate}`;
                }
            }

            // 更新按钮状态
            const btnAll = document.getElementById('btn-preset-all');
            const btnCustom = document.getElementById('btn-preset-custom');
            const customBox = document.getElementById('summary-custom-date-box');

            if (preset === 'all') {
                if (btnAll) btnAll.className = 'btn btn-sm btn-accent';
                if (btnCustom) btnCustom.className = 'btn btn-sm btn-secondary';
                if (customBox) customBox.style.display = 'none';
            } else {
                if (btnAll) btnAll.className = 'btn btn-sm btn-secondary';
                if (btnCustom) btnCustom.className = 'btn btn-sm btn-accent';
                if (customBox) customBox.style.display = 'inline-flex';
            }

            fetch(url)
                .then(res => res.json())
                .then(res => {
                    if (!res.success) {
                        showToast('错误', '加载汇总数据失败', 'error');
                        return;
                    }
                    currentSummaryData = res;
                    renderSummaryKPIs(res);
                    renderSoilSummaryTable(res.by_soil_type || []);
                    renderSiteSummaryTable(res.by_dump_site || []);
                    renderPivotMatrix(res.pivot_matrix || {});
                })
                .catch(err => {
                    console.error('Fetch summary failed:', err);
                    showToast('异常', '加载汇总数据出错', 'error');
                });
        }

        function toggleCustomSummaryDate() {
            const customBox = document.getElementById('summary-custom-date-box');
            if (!customBox) return;
            if (customBox.style.display === 'none') {
                customBox.style.display = 'inline-flex';
                if (currentSummaryData && currentSummaryData.db_range) {
                    document.getElementById('summary-start-date').value = currentSummaryData.db_range.min;
                    document.getElementById('summary-end-date').value = currentSummaryData.db_range.max;
                }
            } else {
                customBox.style.display = 'none';
            }
        }

        function applyCustomSummaryDate() {
            const startDate = document.getElementById('summary-start-date').value;
            const endDate = document.getElementById('summary-end-date').value;
            if (!startDate || !endDate) {
                showToast('提示', '请选择完整起止日期', 'error');
                return;
            }
            loadSummaryAnalytics('custom', startDate, endDate);
        }

        function renderSummaryKPIs(data) {
            const totalOut = data.total_out_trips || 0;
            const evCount = data.ev_count || 0;
            const fuelCount = data.fuel_count || 0;
            
            const evPct = totalOut > 0 ? ((evCount / totalOut) * 100).toFixed(1) : '0.0';
            const fuelPct = totalOut > 0 ? ((fuelCount / totalOut) * 100).toFixed(1) : '0.0';

            document.getElementById('sum-total-trips').innerText = totalOut.toLocaleString('zh-CN');
            document.getElementById('sum-ev-trips').innerText = evCount.toLocaleString('zh-CN');
            document.getElementById('sum-ev-pct').innerText = `(${evPct}%)`;
            document.getElementById('sum-fuel-trips').innerText = fuelCount.toLocaleString('zh-CN');
            document.getElementById('sum-fuel-pct').innerText = `(${fuelPct}%)`;
            
            document.getElementById('sum-sites-cnt').innerText = (data.by_dump_site || []).length;
            document.getElementById('sum-soils-cnt').innerText = (data.by_soil_type || []).length;
        }

        function renderSoilSummaryTable(list) {
            const tbody = document.getElementById('table-body-soil-summary');
            if (!tbody) return;
            if (list.length === 0) {
                tbody.innerHTML = `<tr><td colspan="7" style="color:var(--text-muted);">暂无土方规格汇总数据</td></tr>`;
                return;
            }
            let html = '';
            list.forEach((item, idx) => {
                const costStr = item.total_cost ? `￥${parseFloat(item.total_cost).toLocaleString('zh-CN', {minimumFractionDigits:2, maximumFractionDigits:2})}` : '￥0.00';
                html += `
                    <tr>
                        <td style="font-weight:700;">${idx + 1}</td>
                        <td style="font-weight:700; color:var(--text-primary); text-align:left;">${item.soil_type}</td>
                        <td style="font-weight:800; color:var(--color-out);">${item.trips} 趟</td>
                        <td><span class="direction-pill out" style="width:auto; padding:2px 8px;">${item.percentage}%</span></td>
                        <td>￥${item.unit_price}</td>
                        <td style="font-weight:700; color:${item.is_income === 1 ? 'var(--color-in)' : 'var(--text-primary)'};">${costStr}</td>
                        <td style="font-weight:700; color:var(--color-in);">${item.ev_trips} 趟 (${item.ev_percentage}%)</td>
                    </tr>
                `;
            });
            tbody.innerHTML = html;
        }

        function renderSiteSummaryTable(list) {
            const tbody = document.getElementById('table-body-site-summary');
            if (!tbody) return;
            if (list.length === 0) {
                tbody.innerHTML = `<tr><td colspan="7" style="color:var(--text-muted);">暂无消纳点汇总数据</td></tr>`;
                return;
            }
            let html = '';
            list.forEach((item, idx) => {
                const costStr = item.total_cost ? `￥${parseFloat(item.total_cost).toLocaleString('zh-CN', {minimumFractionDigits:2, maximumFractionDigits:2})}` : '￥0.00';
                html += `
                    <tr>
                        <td style="font-weight:700;">${idx + 1}</td>
                        <td style="font-weight:700; color:var(--text-primary); text-align:left;">${item.dump_site}</td>
                        <td style="font-weight:800; color:var(--color-out);">${item.trips} 趟</td>
                        <td><span class="direction-pill out" style="width:auto; padding:2px 8px;">${item.percentage}%</span></td>
                        <td>￥${item.unit_price}</td>
                        <td style="font-weight:700;">${costStr}</td>
                        <td style="font-weight:700; color:var(--color-in);">${item.ev_trips} 趟 (${item.ev_percentage}%)</td>
                    </tr>
                `;
            });
            tbody.innerHTML = html;
        }

        function renderPivotMatrix(pivotData) {
            const thead = document.getElementById('pivot-thead');
            const tbody = document.getElementById('pivot-tbody');
            if (!thead || !tbody) return;

            const dates = pivotData.dates || [];
            const sites = pivotData.sites || [];

            if (dates.length === 0 || sites.length === 0) {
                thead.innerHTML = '';
                tbody.innerHTML = `<tr><td style="color:var(--text-muted);">暂无交叉透视表数据</td></tr>`;
                return;
            }

            // 表头
            let headHtml = `<tr><th style="position:sticky; left:0; z-index:15; background:var(--table-th-bg); min-width:140px;">消纳场/卸土点</th><th style="min-width:90px;">累计趟数</th>`;
            dates.forEach(d => {
                headHtml += `<th style="min-width:70px; font-size:11px;">${d.slice(5)}</th>`;
            });
            headHtml += `</tr>`;
            thead.innerHTML = headHtml;

            // 数据行
            let bodyHtml = '';
            sites.forEach(siteItem => {
                bodyHtml += `<tr class="pivot-site-row" data-site="${siteItem.dump_site}">`;
                bodyHtml += `<td style="position:sticky; left:0; z-index:5; background:var(--table-th-bg); font-weight:800; text-align:left;">${siteItem.dump_site}</td>`;
                bodyHtml += `<td style="font-weight:800; color:var(--color-out);">${siteItem.total_trips}</td>`;
                
                dates.forEach(d => {
                    const cnt = siteItem.daily_trips[d] || 0;
                    if (cnt > 0) {
                        bodyHtml += `<td><span class="direction-pill out" style="width:auto; padding:1px 6px; font-size:11px;">${cnt}</span></td>`;
                    } else {
                        bodyHtml += `<td style="color:var(--text-muted); opacity:0.3;">-</td>`;
                    }
                });
                bodyHtml += `</tr>`;
            });
            tbody.innerHTML = bodyHtml;
        }

        function filterPivotMatrix() {
            const query = document.getElementById('pivot-search-input').value.trim().toLowerCase();
            const rows = document.querySelectorAll('.pivot-site-row');
            rows.forEach(row => {
                const siteName = (row.getAttribute('data-site') || '').toLowerCase();
                if (siteName.includes(query)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        }

        // ==========================================================================
        // 📤 Excel 台账拖拽与一键上传导入 逻辑
        // ==========================================================================
        let selectedExcelFile = null;

        function handleExcelFileSelect(event) {
            const file = event.target.files[0];
            if (!file) return;
            selectedExcelFile = file;
            document.getElementById('upload-filename').innerText = file.name;
            document.getElementById('upload-status-msg').innerText = `文件可就绪，文件大小: ${(file.size / 1024).toFixed(1)} KB`;
            document.getElementById('upload-preview-box').style.display = 'block';
        }

        function executeExcelUpload() {
            if (!selectedExcelFile) {
                showToast('提示', '请先选择要上传的 Excel 文件', 'error');
                return;
            }
            const btn = document.getElementById('btn-do-import');
            const statusMsg = document.getElementById('upload-status-msg');
            btn.disabled = true;
            statusMsg.innerText = '正在解析 Excel 表格并灌入数据库，请稍候...';

            const formData = new FormData();
            formData.append('file', selectedExcelFile);

            fetch('/api/import_excel', {
                method: 'POST',
                body: formData
            })
            .then(res => res.json())
            .then(res => {
                btn.disabled = false;
                if (res.success) {
                    showToast('成功', res.message, 'success');
                    statusMsg.innerText = `✅ ${res.message}`;
                    loadSummaryAnalytics('all');
                } else {
                    showToast('导入失败', res.detail || res.message, 'error');
                    statusMsg.innerText = `❌ 导入失败: ${res.detail || res.message}`;
                }
            })
            .catch(err => {
                btn.disabled = false;
                showToast('异常', '文件导入出错', 'error');
                statusMsg.innerText = `❌ 导入请求发生网络错误: ${err}`;
            });
        }
"""

content += summary_js_code

with open(html_path, "w", encoding="utf-8") as f:
    f.write(content)

print("[Success] index.html JavaScript 逻辑成功升级！")

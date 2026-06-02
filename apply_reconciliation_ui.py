import os

INDEX_PATH = r"C:\Users\RM\.gemini\antigravity\scratch\worksite_bookkeeping_app\templates\index.html"

with open(INDEX_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add 'Reconciliation' to the sidebar
sidebar_item = """
            <li class="nav-item" data-tab="reconciliation">
                <i data-lucide="calculator"></i>
                <span>结算对账</span>
            </li>
"""
content = content.replace(
    '<li class="nav-item" data-tab="settings">',
    sidebar_item + '\n            <li class="nav-item" data-tab="settings">'
)

# 2. Add the Reconciliation View Container
reconciliation_html = """
        <!-- 对账结算视图 (Reconciliation) -->
        <div id="view-reconciliation" class="view-section" style="display: none;">
            <div class="view-header">
                <h2><i data-lucide="calculator" style="margin-right:8px; color:var(--color-primary);"></i>结算对账单</h2>
                <div class="header-actions">
                    <button class="btn btn-primary" onclick="refreshReconciliation()">
                        <i data-lucide="refresh-cw"></i> 刷新对账单
                    </button>
                </div>
            </div>

            <div class="dashboard-grid" style="grid-template-columns: 1fr; gap: 20px;">
                <!-- 1. 车队对账卡片 -->
                <div class="glass-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                        <h3 class="card-header-title" style="margin-bottom:0; border-left-color: var(--color-out);">
                            <i data-lucide="truck"></i>应付车队运费结算单
                        </h3>
                    </div>
                    <div class="table-responsive">
                        <table class="ledger-table">
                            <thead>
                                <tr>
                                    <th>车队/车主</th>
                                    <th>总拉运(趟)</th>
                                    <th>应付运费(元)</th>
                                    <th>已付(元)</th>
                                    <th>未付(元)</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody id="recon-fleet-body">
                                <tr><td colspan="6" style="text-align:center; color:var(--text-secondary);">加载中...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- 2. 卸土点对账卡片 -->
                <div class="glass-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                        <h3 class="card-header-title" style="margin-bottom:0; border-left-color: var(--color-in);">
                            <i data-lucide="map-pin"></i>应付卸土点结算单
                        </h3>
                    </div>
                    <div class="table-responsive">
                        <table class="ledger-table">
                            <thead>
                                <tr>
                                    <th>卸土点</th>
                                    <th>总拉运(车)</th>
                                    <th>应付卸土费(元)</th>
                                    <th>已付(元)</th>
                                    <th>未付(元)</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody id="recon-site-body">
                                <tr><td colspan="6" style="text-align:center; color:var(--text-secondary);">加载中...</td></tr>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
"""

content = content.replace(
    '<!-- 设置视图 (Settings) -->',
    reconciliation_html + '\n        <!-- 设置视图 (Settings) -->'
)

# 3. Add Javascript for Reconciliation Tab
js_logic = """
        // =============== 结算对账逻辑 ===============
        function refreshReconciliation() {
            fetch(`/api/reconciliation?date=${selectedQueryDate}`)
            .then(res => res.json())
            .then(data => {
                if (!data.success) {
                    showToast('错误', '加载对账数据失败', 'error');
                    return;
                }
                
                // 1. 渲染车队结算单
                const fleetBody = document.getElementById('recon-fleet-body');
                let fleetHtml = '';
                if (data.fleets.length === 0) {
                    fleetHtml = `<tr><td colspan="6" style="text-align:center; color:var(--text-secondary); padding:20px;">当日无车队数据</td></tr>`;
                } else {
                    data.fleets.forEach(f => {
                        const fleetName = f.fleet_name || '个人散车';
                        fleetHtml += `
                            <tr>
                                <td style="font-weight:700;">${fleetName}</td>
                                <td style="color:var(--color-out); font-weight:700;">${f.total_trips} 趟</td>
                                <td style="font-weight:700; color:var(--color-primary);">￥${f.total_cost.toFixed(2)}</td>
                                <td style="color:var(--color-in);">￥${f.paid_amount.toFixed(2)}</td>
                                <td style="color:var(--color-danger); font-weight:700;">￥${f.unpaid_amount.toFixed(2)}</td>
                                <td>
                                    ${f.unpaid_amount > 0 ? `<button class="btn btn-primary" style="padding:2px 8px; font-size:12px;" onclick="batchPay('fleet', '${f.fleet_name}', 'soil', 1)">一键付清运费</button>` : `<span style="color:var(--color-in); font-size:12px; font-weight:600;"><i data-lucide="check-circle" style="width:12px; height:12px; display:inline; margin-bottom:-2px;"></i> 已付清</span>`}
                                </td>
                            </tr>
                        `;
                    });
                }
                fleetBody.innerHTML = fleetHtml;

                // 2. 渲染卸土点结算单
                const siteBody = document.getElementById('recon-site-body');
                let siteHtml = '';
                if (data.sites.length === 0) {
                    siteHtml = `<tr><td colspan="6" style="text-align:center; color:var(--text-secondary); padding:20px;">当日无卸土点数据</td></tr>`;
                } else {
                    data.sites.forEach(s => {
                        const siteName = s.dump_site || '未分配';
                        siteHtml += `
                            <tr>
                                <td style="font-weight:700;">${siteName}</td>
                                <td style="color:var(--color-out); font-weight:700;">${s.total_trips} 车</td>
                                <td style="font-weight:700; color:var(--color-primary);">￥${s.total_cost.toFixed(2)}</td>
                                <td style="color:var(--color-in);">￥${s.paid_amount.toFixed(2)}</td>
                                <td style="color:var(--color-danger); font-weight:700;">￥${s.unpaid_amount.toFixed(2)}</td>
                                <td>
                                    ${s.unpaid_amount > 0 ? `<button class="btn btn-primary" style="padding:2px 8px; font-size:12px;" onclick="batchPay('site', '${s.dump_site}', 'dump', 1)">一键付清卸土费</button>` : `<span style="color:var(--color-in); font-size:12px; font-weight:600;"><i data-lucide="check-circle" style="width:12px; height:12px; display:inline; margin-bottom:-2px;"></i> 已付清</span>`}
                                </td>
                            </tr>
                        `;
                    });
                }
                siteBody.innerHTML = siteHtml;
                lucide.createIcons({attrs: {"stroke-width": 2}});
            })
            .catch(err => {
                showToast('异常', err.toString(), 'error');
            });
        }

        function batchPay(targetType, targetName, feeType, status) {
            fetch('/api/batch_toggle_reconciliation', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    date: selectedQueryDate,
                    target_type: targetType,
                    target_name: targetName,
                    fee_type: feeType,
                    status: status
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast('成功', '批量结清操作成功', 'success');
                    refreshReconciliation();
                    if(currentTab === 'ledger') refreshLedger();
                } else {
                    showToast('失败', data.message || '操作失败', 'error');
                }
            })
            .catch(err => showToast('异常', err.toString(), 'error'));
        }

        // =============== 原有逻辑的补充 ===============
"""

content = content.replace(
    '// 初始化启动',
    js_logic + '\n        // 初始化启动'
)

# 4. Add the tab click hook for reconciliation
content = content.replace(
    "if (tabId === 'settings') refreshSettings();",
    "if (tabId === 'settings') refreshSettings();\n            if (tabId === 'reconciliation') refreshReconciliation();"
)


with open(INDEX_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("Applied Reconciliation Page UI to index.html")

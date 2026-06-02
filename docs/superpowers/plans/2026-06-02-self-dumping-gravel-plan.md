# Self-Dumping Gravel and Seven-Day Seed Data Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将系统内的“级配石（收入类土方）”与消纳点完全解耦，使其在录入、修改和统计时默认记录为“自行消纳”，无卸土费，同时生成包含当天在内的一周高仿真演示数据。

**Architecture:** 
1. 后端在车辆流水录入与修改接口中拦截并自动设定级配石的去向为 `"自行消纳"`，并在台账聚合中将 `"自行消纳"` 从未分配中排除。
2. 前端在流水列表和微调弹窗中屏蔽级配石的卸土费和付款状态切换徽章，联动禁用消纳地选择。
3. 编写 `seed_seven_days.py` 脚本生成连续 7 天的高仿真流水记录以进行功能演练。

**Tech Stack:** Python, FastAPI, SQLite, HTML5, Vanilla JavaScript

---

### Task 1: 后端接口与统计逻辑重构 (`web-server.py`)

**Files:**
- Modify: `web-server.py`

- [ ] **Step 1: 修改手工补录接口 `/api/manual_import`**
  若土方类型是级配石，强制设定 `dump_site` 为 `"自行消纳"` 且设定 `soil_paid` 为 1。
  ```python
  # 修改前 (约 376-382 行):
  # soil_paid = 1 if req.soil_type == "级配石" else 0
  # cursor.execute(..., (..., dump_site, req.soil_type, soil_paid))
  
  # 修改后:
  dump_site = req.dump_site
  if req.soil_type == "级配石":
      soil_paid = 1
      dump_site = "自行消纳"
  else:
      soil_paid = 0
  ```

- [ ] **Step 2: 修改单趟记账补录接口 `/api/add_manual_trip`**
  若土方类型是级配石，强制设定 `dump_site` 为 `"自行消纳"` 且设定 `soil_paid` 为 1。
  ```python
  # 修改前 (约 809-814 行):
  # soil_paid = 1 if req.soil_type == "级配石" else 0
  
  # 修改后:
  dump_site = req.dump_site
  if req.soil_type == "级配石":
      soil_paid = 1
      dump_site = "自行消纳"
  else:
      soil_paid = 0
  ```

- [ ] **Step 3: 修改微调目的地接口 `/api/adjust_trip_destination`**
  若微调时更改为级配石，强制设定消纳场为 `"自行消纳"`。
  ```python
  # 修改前 (约 753-757 行):
  # if req.soil_type == "级配石":
  #     cursor.execute("UPDATE vehicle_records SET dump_site = ?, soil_type = ?, soil_paid = 1 WHERE id = ?", (req.dump_site, req.soil_type, req.record_id))
  
  # 修改后:
  if req.soil_type == "级配石":
      cursor.execute("UPDATE vehicle_records SET dump_site = '自行消纳', soil_type = ?, soil_paid = 1, dump_paid = 1 WHERE id = ?", (req.soil_type, req.record_id))
  ```

- [ ] **Step 4: 修改待审计对账出场趟数（未分配趟数）统计逻辑**
  在 KPI 统计里过滤掉级配石相关的趟数。
  ```python
  # 修改前 (约 1367-1372 行):
  # SELECT COUNT(*) FROM vehicle_records WHERE direction = 'OUT' AND (dump_site = '未分配' OR dump_site IS NULL) AND pass_time BETWEEN ? AND ?
  
  # 修改后:
  # SELECT COUNT(*) FROM vehicle_records WHERE direction = 'OUT' AND (dump_site = '未分配' OR dump_site IS NULL) AND soil_type != '级配石' AND pass_time BETWEEN ? AND ?
  ```

- [ ] **Step 5: 修改 `/api/records` 与 `/api/ledger` 的 `ledger_map` 聚合逻辑**
  在聚合车辆台账时，对消纳地为 `"自行消纳"` 的情况予以放行，不计入任何消纳点趟数，也不计入未分配趟数。
  ```python
  # 修改前 (在 /api/ledger 和 /api/records 两处，分别位于 614 行和 1482 行附近):
  # if dump_site in site_names:
  #     ledger_map[plate_no]["site_trips"][dump_site] += trip_cnt
  # else:
  #     ledger_map[plate_no]["unassigned_trips"] += trip_cnt
  
  # 修改后:
  if dump_site in site_names:
      ledger_map[plate_no]["site_trips"][dump_site] += trip_cnt
  elif dump_site == "自行消纳":
      pass
  else:
      ledger_map[plate_no]["unassigned_trips"] += trip_cnt
  ```

- [ ] **Step 6: 检查并提交后端改动**
  运行后端服务以确保编译和启动正常。
  ```bash
  python web-server.py
  ```

---

### Task 2: 前端流水与微调弹窗重构 (`templates/index.html`)

**Files:**
- Modify: `templates/index.html`

- [ ] **Step 1: 修改详细对账流水表格渲染 (在 `refreshLedger` 内部)**
  消纳费付款一列在 `"自行消纳"` 时直接渲染为文本 `"自行消纳"`。
  ```javascript
  // 修改前 (约 3470 行附近):
  // let dumpPaymentHtml = '';
  // if (isUnassigned) { ... } else { ... }
  
  // 修改后:
  const isSelfDump = (r.dump_site === '自行消纳');
  let dumpPaymentHtml = '';
  if (isSelfDump) {
      dumpPaymentHtml = `<span style="color:var(--text-muted); font-size:12px;">自行消纳</span>`;
  } else if (isUnassigned) {
      dumpPaymentHtml = `<span style="color:var(--text-muted); font-size:12px;">—</span>`;
  } else {
      ...
  }
  ```

- [ ] **Step 2: 优化对账弹窗的车辆趟数渲染 (`renderAdjustTrips`)**
  增加对 `"自行消纳"` 消纳点的支持。若该趟为级配石，直接禁用下拉选择并选中 `"自行消纳"`；若非级配石，则允许选择 `"自行消纳"` 以及其他消纳场。
  ```javascript
  // 修改前 (约 4096-4103 行附近):
  // const siteName = r.dump_site || '未分配';
  // let selectHtml = `<select class="input-control" ...>`;
  
  // 修改后:
  const isGravel = (r.soil_type === '级配石');
  const siteName = r.dump_site || (isGravel ? '自行消纳' : '未分配');
  let selectHtml = '';
  if (isGravel) {
      selectHtml = `<select class="input-control" style="width: 150px; padding: 4px 6px; font-size:12px; height: 30px;" disabled>`;
      selectHtml += `<option value="自行消纳" selected>分账：自行消纳</option>`;
      selectHtml += `</select>`;
  } else {
      selectHtml = `<select class="input-control" style="width: 150px; padding: 4px 6px; font-size:12px; height: 30px;" onchange="submitSingleAdjust(${r.id}, this.value, '${r.soil_type}')">`;
      selectHtml += `<option value="未分配" ${siteName === '未分配' ? 'selected' : ''}>分账：未分配</option>`;
      selectHtml += `<option value="自行消纳" ${siteName === '自行消纳' ? 'selected' : ''}>分账：自行消纳</option>`;
      currentSitesList.forEach(s => {
          selectHtml += `<option value="${s.name}" ${siteName === s.name ? 'selected' : ''}>分账：${s.name}</option>`;
      });
      selectHtml += `</select>`;
  }
  ```

- [ ] **Step 3: 检查并提交前端改动**
  检查前端代码保存无误。

---

### Task 3: 演示数据 Seed 脚本编写与运行

**Files:**
- Create: `seed_seven_days.py`

- [ ] **Step 1: 编写 `seed_seven_days.py` 代码**
  编写包含 7 天（2026-05-27 至 2026-06-02）高仿真流水的数据灌入脚本。级配石默认归档为 `"自行消纳"`，无消纳费，单价为 150 元/趟，`is_income = 1`。其他常规土方指派普通消纳点，运费和消纳费支付状态随机。
  （代码具体内容见后续实现阶段）

- [ ] **Step 2: 运行 Seed 脚本**
  执行该 Python 脚本完成数据库更新。
  ```bash
  python seed_seven_days.py
  ```
  预期：输出 "7 days of high-fidelity seed data generated successfully!" 并将数据录入到数据库。

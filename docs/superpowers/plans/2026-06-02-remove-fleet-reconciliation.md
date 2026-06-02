# 废弃车队维度并改为单车运费结算 实施计划 (Implementation Plan)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 彻底移除系统中的车队维度数据与管理功能，将“应付车队运费结算单”改造为直接按“单车（车牌号）”进行结算对账，摆脱繁琐的车队名册维护。

**Architecture:**
1. **后端 (FastAPI/SQLite)**：
   * 废弃 `frequent_plates` 表中的 `company_name` 绑定。
   * 修改 `/api/reconciliation`，改为按 `plate_no` 进行聚合。返回的 `fleets` 数组内，用车牌号作为 `company_name` 键的值，从而以最小改动复用前端现有的数据流。
   * 修改 `/api/batch_toggle_reconciliation`，当 `target_type == "fleet"`（兼容原有参数）时，直接按车牌号更新对应车辆今日全部拉运记录的运费付款状态 (`soil_paid`)。
   * 废弃并移除 `/api/bind_vehicle_fleet` 路由及相关的 Schema。
2. **前端 (HTML/CSS/JS)**：
   * 对账面板：重命名“应付车队运费结算单”为“应付单车运费结算单”，列表展示所有单车的趟数及运费金额，并首列使用高保真拟真车牌渲染。
   * 配置面板：删除“车队与车辆名册管理”卡片，调整布局使左侧的“场地价格”与“土方类型”配置拉宽占满容器。
   * 去向微调弹窗：移除“绑定归属车队”部分。
3. **测试种子脚本**：
   * 简化 `reseed_real_vehicles.py` 和 `seed_test_data.py`，不再生成虚拟的车队，直接统归为 `"个人车主"`。

**Tech Stack:** Python (FastAPI), SQLite, HTML, CSS, JavaScript (Vanilla ES6)

---

## 详细执行步骤 (Tasks & Checklist)

### Task 1: 修改后端 `web-server.py` 的数据处理与结算路由

**Files:**
- Modify: `c:/Users/scodi.KYLINX/Desktop/Chinese_license_plate_detection_recognition/web-server.py`

- [ ] **Step 1: 删除车队绑定路由和入参声明**
  删除 `class BindVehicleFleetRequest(BaseModel)` 声明及 `@app.post("/api/bind_vehicle_fleet")`。

- [ ] **Step 2: 修改 `/api/reconciliation` 对账汇总聚合逻辑**
  在 `get_reconciliation_data` 方法中，将按 `company_name` 累加修改为按 `plate_no` 累加。
  ```python
  fleet_map = {}
  for r in records:
      plate = r["plate_no"]
      c_name = plate
      s_type = r["soil_type"] or "渣土"
      ...
  ```

- [ ] **Step 3: 修改 `/api/batch_toggle_reconciliation` 批量结算状态路由**
  直接根据 `req.target_name` 更新对应的 `soil_paid` 状态。

- [ ] **Step 4: 修改车辆出场明细 `/api/vehicle_out_records` 里的车队字段**
  将 `company_name` 统一赋值为 `"个人车主"`。

- [ ] **Step 5: 修改备案车辆同步与常用车牌添加接口**
  将 `sync_registered_vehicles` 中新增记录时的 `company_name` 强制指定为 `"个人车主"`。

- [ ] **Step 6: 手动调用测试脚本或 HTTP 请求确认接口数据结构无误**
  检查 `/api/reconciliation` 返回的值中的 `fleets` 项。

---

### Task 2: 修改前端 `templates/index.html` 的 UI 与渲染脚本

**Files:**
- Modify: `c:/Users/scodi.KYLINX/Desktop/Chinese_license_plate_detection_recognition/templates/index.html`

- [ ] **Step 1: 调整参数配置面板的 CSS 栅格，占满整宽**
  将 `#panel-config.active` 的 `grid-template-columns` 属性变更为单列：
  ```css
  #panel-config.active {
      display: grid;
      grid-template-columns: 1fr;
      gap: 20px;
  }
  ```

- [ ] **Step 2: 移除“车队与车辆名册管理”卡片 HTML**
  删除 `id="panel-config"` 下的右侧卡片。

- [ ] **Step 3: 修改对账结算单标题、表头并引入车牌 Badge 渲染**
  * 在 `#panel-reconcile` 中将“应付车队运费结算单”更改为“应付单车运费结算单”；
  * 修改检索 placeholder 为“检索车牌...”；
  * 表头 `<th>车队/车主</th>` 改为 `<th>车牌号码</th>`；
  * 修改 `renderReconciliationLists` 函数中的 `fleetHtml` 拼接逻辑。

- [ ] **Step 4: 移除微调弹窗中绑定归属车队的 DOM 结构**
  在弹窗 `#adjust-modal` 内，移除归属车队绑定的 HTML。

- [ ] **Step 5: 移除 JS 部分对车队操作的无用逻辑**
  删除 `submitBindVehicleFleet()`、`unbindVehicleFromFleet()`、`renderFleetManager()` 等前端 JS 逻辑。

---

### Task 3: 简化数据种子生成脚本

**Files:**
- Modify: `c:/Users/scodi.KYLINX/Desktop/Chinese_license_plate_detection_recognition/reseed_real_vehicles.py`
- Modify: `c:/Users/scodi.KYLINX/Desktop/Chinese_license_plate_detection_recognition/seed_test_data.py`

- [ ] **Step 1: 修改 `reseed_real_vehicles.py`**
  常用车牌在初始化时，车队名称固定插入为 `"个人车主"`。

- [ ] **Step 2: 修改 `seed_test_data.py`**
  移除按车队名分配车辆测试数据的累加逻辑，将常用车牌车队均设为 `"个人车主"`。

---

## Verification Plan

### 自动接口验证 (使用 Python 临时测试脚本)
1. 创建测试脚本 `verify_endpoints.py`。
2. 运行该测试脚本验证接口返回值。

### 手工 UI 功能验证
1. 打开浏览器登录系统，进入“结算汇总对账”面板；
2. 观察左侧卡片标题、表头和车牌 Badge 渲染是否正常；
3. 测试一键付清/设为未付状态切换；
4. 确认系统配置面板中右侧的“车队管理名册”已消失；
5. 点击列表内单车的对账按钮，检查弹出的微调窗口中，仅有默认去向和单次行程微调，没有“归属车队”配置框。

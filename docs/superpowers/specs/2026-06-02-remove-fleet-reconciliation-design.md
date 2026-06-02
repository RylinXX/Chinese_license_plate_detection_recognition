# 废弃车队维度并改为单车运费结算设计说明书 (Design Spec)

## 1. 背景与目标
在原先的运费结算流程中，系统需要维护“车队”信息，并将各通行车辆划分至指定车队。但由于实际业务中每天来结算的车队并不固定，且维护车队归属名册较为繁琐。
为了简化流程，用户决定废弃“车队”概念，将应付运费结算汇总直接精确到**单个车辆（车牌号）**。结算时只需根据车队提供的车牌列表，分别付清各车运费即可，从而彻底摆脱对车队维护的依赖。

---

## 2. 变更范围及详细设计

### 2.1 后端 API 变更
涉及文件: [web-server.py](file:///c:/Users/scodi.KYLINX/Desktop/Chinese_license_plate_detection_recognition/web-server.py)

#### 1) 每日对账数据获取接口 `/api/reconciliation` (GET)
* **原逻辑**：
  * 从 `vehicle_records` 中获取当天所有出场记录，通过 `LEFT JOIN frequent_plates` 关联获得各车的 `company_name`（车队名），并将运费及付款状态累加到对应的车队上。
* **新逻辑**：
  * 不再通过 `company_name` 进行分组。
  * 改为直接按 **`plate_no`（车牌号）** 进行分组聚合。
  * 返回的数据结构中，`fleets` 键名可以保持或变更为 `vehicles`。为了保证前端的最小化改动与语义清晰，在返回的 JSON 中，我们将原 `fleets` 数组里的每一项改为单车结构：
    ```json
    {
      "company_name": "粤B12345", // 直接以车牌号作为标识，便于前端重用渲染逻辑
      "total_trips": 5,
      "total_cost": 300.0,
      "paid_cost": 180.0,
      "unpaid_cost": 120.0,
      "paid_trips": 3,
      "unpaid_trips": 2
    }
    ```
    *注：通过将 `company_name` 键的值设为车牌号，可以最大化兼容前端原有的渲染绑定逻辑，无需大范围修改 JS 代码中的属性名。*

#### 2) 批量更新结算状态接口 `/api/batch_toggle_reconciliation` (POST)
* **原逻辑**：
  * 当 `req.target_type == "fleet"` 时，如果 `target_name` 为 "个人车主"，则更新所有散车的付款状态；如果为具体车队，则通过子查询更新属于该车队所有车辆的 `soil_paid` 状态。
* **新逻辑**：
  * 将 `target_type` 变更为支持 `"vehicle"` 类型。
  * 当 `target_type == "vehicle"` 时，`target_name` 传入的具体值即为车牌号。
  * 执行 SQL 更新该车在指定日期的运费支付状态：
    ```sql
    UPDATE vehicle_records 
    SET soil_paid = ?
    WHERE direction = 'OUT' AND pass_time BETWEEN ? AND ? AND plate_no = ?
    ```

#### 3) 车队绑定接口 `/api/bind_vehicle_fleet` (POST)
* **变更**：
  * 废弃此 API。可以直接删除或让其返回成功但不作任何操作。建议直接删除相关路由和请求参数定义 `BindVehicleFleetRequest`。

---

### 2.2 前端界面与交互变更
涉及文件: [templates/index.html](file:///c:/Users/scodi.KYLINX/Desktop/Chinese_license_plate_detection_recognition/templates/index.html)

#### 1) 对账结算面板 (`#panel-reconcile`)
* **应付车队运费结算单（左侧卡片）**：
  * 卡片标题从 `应付车队运费结算单` 变更为 `应付单车运费结算单`。
  * 搜索框 `#recon-fleet-search` 的占位符从 `检索车队...` 改为 `检索车牌...`。
  * 表格首列的标题从 `车队/车主` 变更为 `车牌号码`。
  * 渲染每一行数据时，第一列的车牌号使用拟真车牌徽章样式渲染（调用现有的 `renderPlateBadge` 函数）。
  * 结清与重置未付的按钮文案及点击事件保持，调用 `batchPay('fleet', ...)` 时，第二个参数传入的即为车牌号本身。
  * 底部的汇总指标小卡片（总趟数、应付总运费、已结清、未结清）的数据累加逻辑保持不变，但其统计范围从“所有车队”自然过渡为“所有单车”。

#### 2) 系统参数配置面板 (`#panel-config`)
* **车队与车辆名册管理（右侧卡片）**：
  * 彻底从 HTML 中移除该卡片元素 (`<div class="glass-card config-panel" style="display:flex; flex-direction:column; min-height: 550px;">`)。
  * 为了布局的美观，原本平分屏幕的左侧“卸土点价格与土方类型配置”卡片将通过修改 CSS/样式，拉宽至占满一整行或并排平铺，消除右侧空缺。

#### 3) 单车微调弹窗 (`#adjust-modal`)
* **车队归属部分**：
  * 移除绑定车队的下拉菜单选择和绑定按钮（即 `#adjust-vehicle-fleet` 所在的一整个 `form-group` 容器）。

---

### 2.3 测试数据生成器变更
涉及文件:
1. [reseed_real_vehicles.py](file:///c:/Users/scodi.KYLINX/Desktop/Chinese_license_plate_detection_recognition/reseed_real_vehicles.py)
2. [seed_test_data.py](file:///c:/Users/scodi.KYLINX/Desktop/Chinese_license_plate_detection_recognition/seed_test_data.py)

* **变更内容**：
  * 移除所有虚拟车队名册（如 `老张车队`、`李总车队` 等）的定义与随机分配逻辑。
  * 常用车牌在初始化时，`company_name` 统一设置为空或 `"个人车主"`。

---

## 3. 验证方案
1. **静态检查**：确保后端无编译/运行错误，数据库中无孤立的外键约束（该数据库本身未使用车队外键，均存储为字符串）。
2. **接口测试**：
   * 模拟请求 `/api/reconciliation`，确认返回的 `fleets` 数组内每个元素代表单辆车（即 `company_name` 为车牌号，且运力及金额计算正确）。
   * 模拟调用 `/api/batch_toggle_reconciliation`，传入车牌号，验证该车当天的通行运费付款状态更新成功。
3. **界面测试**：
   * 启动 Web 服务，进入“结算汇总对账”选项卡，查看左侧“应付单车运费结算单”是否渲染出漂亮的车牌徽章，并测试检索与“一键付清”按钮是否正常响应。
   * 进入“系统参数配置”选项卡，确认右侧的“车队管理”区域已消失，且布局整体协调。
   * 点击单车的“对账”微调弹窗，确认已不再显示车队绑定表单。

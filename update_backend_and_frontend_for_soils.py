# -*- coding: UTF-8 -*-
import os
import re

def update_backend():
    server_path = "web-server.py"
    if not os.path.exists(server_path):
        print(f"Error: {server_path} not found.")
        return False
        
    with open(server_path, "r", encoding="utf-8") as f:
        code = f.read()

    # 1. 在 init_db 中添加创建 soil_types 表和灌入默认土质价格的逻辑
    old_db_init = """    # 创建 vehicle_bindings 车辆默认去向绑定表"""
    new_db_init = """    # 创建 soil_types 土方价格配置表
    cursor.execute(\"\"\"
        CREATE TABLE IF NOT EXISTS soil_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            unit_price REAL NOT NULL DEFAULT 0.0
        )
    \"\"\")
    
    # 填充默认的土方单价
    cursor.execute("SELECT COUNT(*) FROM soil_types")
    if cursor.fetchone()[0] == 0:
        default_soils = [
            ("渣土", 60.0),
            ("好土", 80.0),
            ("二混子", 100.0),
            ("自卸", 120.0),
            ("级配石", 150.0)
        ]
        cursor.executemany("INSERT INTO soil_types (name, unit_price) VALUES (?, ?)", default_soils)
        print("[Database] 默认土方单价灌入成功。")
        
    # 创建 vehicle_bindings 车辆默认去向绑定表"""

    code = code.replace(old_db_init, new_db_init)

    # 2. 添加 Pydantic 请求模型 SoilTypeRequest
    old_pydantic = """class DumpSiteRequest(BaseModel):
    name: str
    unit_price: float"""
    
    new_pydantic = """class DumpSiteRequest(BaseModel):
    name: str
    unit_price: float

class SoilTypeRequest(BaseModel):
    name: str
    unit_price: float"""

    code = code.replace(old_pydantic, new_pydantic)

    # 3. 添加 /api/soil_types 的 GET/POST/PUT/DELETE API 路由
    soil_routes = """
@app.get("/api/soil_types")
def get_soil_types() -> list[dict[str, Any]]:
    \"\"\"获取所有土方类型及单价\"\"\"
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, unit_price FROM soil_types ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r["id"], "name": r["name"], "unit_price": r["unit_price"]} for r in rows]

@app.post("/api/soil_types")
def add_soil_type(req: SoilTypeRequest) -> dict[str, Any]:
    \"\"\"添加新土方类型\"\"\"
    name = req.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="土方类型名称不能为空")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO soil_types (name, unit_price) VALUES (?, ?)", (name, req.unit_price))
        conn.commit()
        conn.close()
        return {"success": True, "message": f"成功添加土方类型 {name}"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="该土方类型已存在")

@app.put("/api/soil_types/{soil_id}")
def update_soil_type(soil_id: int, req: SoilTypeRequest) -> dict[str, Any]:
    \"\"\"修改指定的土方类型单价\"\"\"
    name = req.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="土方类型名称不能为空")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM soil_types WHERE name = ? AND id != ?", (name, soil_id))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="该土方类型名称已存在")
        
    cursor.execute("SELECT name FROM soil_types WHERE id = ?", (soil_id,))
    old_row = cursor.fetchone()
    if not old_row:
        conn.close()
        raise HTTPException(status_code=404, detail="未找到该土方类型")
    old_name = old_row[0]
    
    cursor.execute("UPDATE soil_types SET name = ?, unit_price = ? WHERE id = ?", (name, req.unit_price, soil_id))
    # 级联更新通行记录里的土方类型名称
    cursor.execute("UPDATE vehicle_records SET soil_type = ? WHERE soil_type = ?", (name, old_name))
    conn.commit()
    conn.close()
    return {"success": True, "message": f"成功修改土方类型为 {name}"}

@app.delete("/api/soil_types/{soil_id}")
def delete_soil_type(soil_id: int) -> dict[str, Any]:
    \"\"\"删除指定的土方类型\"\"\"
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM soil_types WHERE id = ?", (soil_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="未找到该土方类型")
    soil_name = row[0]
    
    cursor.execute("DELETE FROM soil_types WHERE id = ?", (soil_id,))
    # 级联修改已删除的类型为剩下列表中第一个或默认渣土
    cursor.execute("SELECT name FROM soil_types LIMIT 1")
    fallback_row = cursor.fetchone()
    fallback_name = fallback_row[0] if fallback_row else "渣土"
    cursor.execute("UPDATE vehicle_records SET soil_type = ? WHERE soil_type = ?", (fallback_name, soil_name))
    conn.commit()
    conn.close()
    return {"success": True, "message": f"成功删除土方类型 {soil_name}"}
"""

    # 匹配在 @app.get("/api/ledger") 路由之前插入这些路由
    code = code.replace('@app.get("/api/ledger")', soil_routes + '\n@app.get("/api/ledger")')

    # 4. 重构 get_daily_ledger 计算费用的 SQL 和聚合逻辑 (按土方价格计费)
    old_ledger_api_block = """@app.get("/api/ledger")
def get_daily_ledger(date: str | None = Query(None, description="格式 YYYY-MM-DD，默认今天")) -> dict[str, Any]:
    \"\"\"获取指定日期的每日台账\"\"\"
    current_today = datetime.now().strftime("%Y-%m-%d")
    if not date:
        date = current_today
        
    query_start = f"{date} 00:00:00"
    query_end = f"{date} 23:59:59"
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. 查询所有卸土点及价格
    cursor.execute("SELECT id, name, unit_price FROM dump_sites ORDER BY id ASC")
    rows_sites = cursor.fetchall()
    sites = [{"id": r["id"], "name": r["name"], "unit_price": r["unit_price"]} for r in rows_sites]
    site_names = [s["name"] for s in sites]
    site_prices = {s["name"]: s["unit_price"] for s in sites}
    
    # 2. 查询该日出场车辆及其卸土点去向记录计数
    cursor.execute(\"\"\"
        SELECT plate_no, plate_color, dump_site, COUNT(*) as trip_cnt 
        FROM vehicle_records 
        WHERE direction = 'OUT' AND pass_time BETWEEN ? AND ?
        GROUP BY plate_no, dump_site
    \"\"\", (query_start, query_end))
    rows = cursor.fetchall()
    
    # 3. 按车牌聚合趟数
    ledger_map = {}
    for r in rows:
        plate_no = r["plate_no"]
        plate_color = r["plate_color"] or "蓝色"
        dump_site = r["dump_site"] or "未分配"
        trip_cnt = r["trip_cnt"]
        
        if plate_no not in ledger_map:
            ledger_map[plate_no] = {
                "plate_no": plate_no,
                "plate_color": plate_color,
                "site_trips": {s_name: 0 for s_name in site_names},
                "unassigned_trips": 0,
                "total_trips": 0,
                "total_cost": 0.0
            }
        
        if dump_site in site_names:
            ledger_map[plate_no]["site_trips"][dump_site] = trip_cnt
            ledger_map[plate_no]["total_cost"] += trip_cnt * site_prices[dump_site]
        else:
            ledger_map[plate_no]["unassigned_trips"] += trip_cnt
            
        ledger_map[plate_no]["total_trips"] += trip_cnt
        
    ledger_rows = list(ledger_map.values())
    # 按照出场总趟数和今日总账金额降序排列
    ledger_rows.sort(key=lambda x: (x["total_trips"], x["total_cost"]), reverse=True)
    
    # 4. 计算各个土点今日汇总信息（车数、趟数、总金额）
    site_summaries = []
    for s_name in site_names:
        s_price = site_prices[s_name]
        trips_sum = sum(item["site_trips"].get(s_name, 0) for item in ledger_rows)
        trucks_sum = sum(1 for item in ledger_rows if item["site_trips"].get(s_name, 0) > 0)
        site_summaries.append({
            "site_name": s_name,
            "unit_price": s_price,
            "total_trips": trips_sum,
            "total_trucks": trucks_sum,
            "total_cost": trips_sum * s_price
        })
        
    # 未分配汇总
    total_unassigned_trips = sum(item["unassigned_trips"] for item in ledger_rows)
    unassigned_trucks = sum(1 for item in ledger_rows if item["unassigned_trips"] > 0)
    
    conn.close()
    
    return {
        "success": True,
        "selected_date": date,
        "dump_sites": sites,
        "ledger_rows": ledger_rows,
        "site_summaries": site_summaries,
        "unassigned_summary": {
            "total_trips": total_unassigned_trips,
            "total_trucks": unassigned_trucks
        }
    }"""

    new_ledger_api_block = """@app.get("/api/ledger")
def get_daily_ledger(date: str | None = Query(None, description="格式 YYYY-MM-DD，默认今天")) -> dict[str, Any]:
    \"\"\"获取指定日期的每日台账 (按土方单价结算)\"\"\"
    current_today = datetime.now().strftime("%Y-%m-%d")
    if not date:
        date = current_today
        
    query_start = f"{date} 00:00:00"
    query_end = f"{date} 23:59:59"
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. 查询所有卸土点
    cursor.execute("SELECT id, name FROM dump_sites ORDER BY id ASC")
    rows_sites = cursor.fetchall()
    sites = [{"id": r["id"], "name": r["name"]} for r in rows_sites]
    site_names = [s["name"] for s in sites]
    
    # 1.1 查询所有土方类型单价
    cursor.execute("SELECT id, name, unit_price FROM soil_types ORDER BY id ASC")
    rows_soils = cursor.fetchall()
    soils = [{"id": r["id"], "name": r["name"], "unit_price": r["unit_price"]} for r in rows_soils]
    soil_prices = {s["name"]: s["unit_price"] for s in soils}
    
    # 2. 查询该日出场车辆及其卸土点去向与土方记录计数
    cursor.execute(\"\"\"
        SELECT plate_no, plate_color, dump_site, soil_type, COUNT(*) as trip_cnt 
        FROM vehicle_records 
        WHERE direction = 'OUT' AND pass_time BETWEEN ? AND ?
        GROUP BY plate_no, dump_site, soil_type
    \"\"\", (query_start, query_end))
    rows = cursor.fetchall()
    
    # 3. 按车牌聚合趟数与金额
    ledger_map = {}
    for r in rows:
        plate_no = r["plate_no"]
        plate_color = r["plate_color"] or "蓝色"
        dump_site = r["dump_site"] or "未分配"
        soil_type = r["soil_type"] or "渣土"
        trip_cnt = r["trip_cnt"]
        price = soil_prices.get(soil_type, 0.0)
        cost_val = trip_cnt * price
        
        if plate_no not in ledger_map:
            ledger_map[plate_no] = {
                "plate_no": plate_no,
                "plate_color": plate_color,
                "site_trips": {s_name: 0 for s_name in site_names},
                "unassigned_trips": 0,
                "total_trips": 0,
                "total_cost": 0.0
            }
        
        if dump_site in site_names:
            ledger_map[plate_no]["site_trips"][dump_site] += trip_cnt
        else:
            ledger_map[plate_no]["unassigned_trips"] += trip_cnt
            
        ledger_map[plate_no]["total_trips"] += trip_cnt
        ledger_map[plate_no]["total_cost"] += cost_val
        
    ledger_rows = list(ledger_map.values())
    # 按照出场总趟数和今日总账金额降序排列
    ledger_rows.sort(key=lambda x: (x["total_trips"], x["total_cost"]), reverse=True)
    
    # 4. 计算各个土点今日汇总信息（车数、趟数、总金额）
    site_summaries = []
    for s_name in site_names:
        trips_sum = sum(item["site_trips"].get(s_name, 0) for item in ledger_rows)
        trucks_sum = sum(1 for item in ledger_rows if item["site_trips"].get(s_name, 0) > 0)
        
        # 计算该土点下的运费汇总 (基于土方价格)
        cursor.execute(\"\"\"
            SELECT SUM(COALESCE(st.unit_price, 0))
            FROM vehicle_records vr
            LEFT JOIN soil_types st ON vr.soil_type = st.name
            WHERE vr.direction = 'OUT' AND vr.dump_site = ? AND vr.pass_time BETWEEN ? AND ?
        \"\"\", (s_name, query_start, query_end))
        cost_sum = cursor.fetchone()[0] or 0.0
        
        site_summaries.append({
            "site_name": s_name,
            "unit_price": 0.0,
            "total_trips": trips_sum,
            "total_trucks": trucks_sum,
            "total_cost": cost_sum
        })
        
    # 未分配汇总
    total_unassigned_trips = sum(item["unassigned_trips"] for item in ledger_rows)
    unassigned_trucks = sum(1 for item in ledger_rows if item["unassigned_trips"] > 0)
    
    conn.close()
    
    return {
        "success": True,
        "selected_date": date,
        "dump_sites": sites,
        "soil_types": soils,
        "ledger_rows": ledger_rows,
        "site_summaries": site_summaries,
        "unassigned_summary": {
            "total_trips": total_unassigned_trips,
            "total_trucks": unassigned_trucks
        }
    }"""

    code = code.replace(old_ledger_api_block, new_ledger_api_block)

    # 5. 更新今日结算金额指标计算: 加入与 soil_types 表的 JOIN (基于土方类型计费)
    old_total_cost_sql = """    # 3.1 统计今日结算总金额
    cursor.execute(\"\"\"
        SELECT SUM(ds.unit_price)
        FROM vehicle_records vr
        JOIN dump_sites ds ON vr.dump_site = ds.name
        WHERE vr.direction = 'OUT' AND vr.pass_time BETWEEN ? AND ?
    \"\"\", (query_start, query_end))"""
    
    new_total_cost_sql = """    # 3.1 统计今日结算总金额 (根据土方单价计算)
    cursor.execute(\"\"\"
        SELECT SUM(st.unit_price)
        FROM vehicle_records vr
        JOIN soil_types st ON vr.soil_type = st.name
        WHERE vr.direction = 'OUT' AND vr.pass_time BETWEEN ? AND ?
    \"\"\", (query_start, query_end))"""

    code = code.replace(old_total_cost_sql, new_total_cost_sql)

    # 6. 更新 /api/analytics 统计分析路由
    # 卸土点统计 (site_summaries 价格采用土方单价)
    old_analytics_sites_sql = """    cursor.execute(\"\"\"
        SELECT vr.dump_site as site_name,
               COUNT(*) as trips,
               COUNT(DISTINCT vr.plate_no) as trucks,
               SUM(CASE WHEN ds.unit_price IS NOT NULL THEN ds.unit_price ELSE 0 END) as cost
        FROM vehicle_records vr
        LEFT JOIN dump_sites ds ON vr.dump_site = ds.name
        WHERE vr.direction = 'OUT' AND vr.pass_time BETWEEN ? AND ?
        GROUP BY vr.dump_site
        ORDER BY trips DESC
    \"\"\", (query_start, query_end))"""
    
    new_analytics_sites_sql = """    cursor.execute(\"\"\"
        SELECT vr.dump_site as site_name,
               COUNT(*) as trips,
               COUNT(DISTINCT vr.plate_no) as trucks,
               SUM(COALESCE(st.unit_price, 0)) as cost
        FROM vehicle_records vr
        LEFT JOIN soil_types st ON vr.soil_type = st.name
        WHERE vr.direction = 'OUT' AND vr.pass_time BETWEEN ? AND ?
        GROUP BY vr.dump_site
        ORDER BY trips DESC
    \"\"\", (query_start, query_end))"""
    
    code = code.replace(old_analytics_sites_sql, new_analytics_sites_sql)

    # 6.2 土质占比分析
    old_analytics_soils_sql = """    cursor.execute(\"\"\"
        SELECT vr.soil_type,
               COUNT(*) as trips,
               COUNT(DISTINCT vr.plate_no) as trucks,
               SUM(CASE WHEN ds.unit_price IS NOT NULL THEN ds.unit_price ELSE 0 END) as cost
        FROM vehicle_records vr
        LEFT JOIN dump_sites ds ON vr.dump_site = ds.name
        WHERE vr.direction = 'OUT' AND vr.pass_time BETWEEN ? AND ?
        GROUP BY vr.soil_type
        ORDER BY trips DESC
    \"\"\", (query_start, query_end))"""
    
    new_analytics_soils_sql = """    cursor.execute(\"\"\"
        SELECT vr.soil_type,
               COUNT(*) as trips,
               COUNT(DISTINCT vr.plate_no) as trucks,
               SUM(COALESCE(st.unit_price, 0)) as cost
        FROM vehicle_records vr
        LEFT JOIN soil_types st ON vr.soil_type = st.name
        WHERE vr.direction = 'OUT' AND vr.pass_time BETWEEN ? AND ?
        GROUP BY vr.soil_type
        ORDER BY trips DESC
    \"\"\", (query_start, query_end))"""
    
    code = code.replace(old_analytics_soils_sql, new_analytics_soils_sql)

    # 6.3 15天每日走势分析
    old_analytics_daily_sql = """    cursor.execute(\"\"\"
        SELECT substr(vr.pass_time, 1, 10) as day_date,
               COUNT(*) as trips,
               SUM(CASE WHEN ds.unit_price IS NOT NULL THEN ds.unit_price ELSE 0 END) as cost
        FROM vehicle_records vr
        LEFT JOIN dump_sites ds ON vr.dump_site = ds.name
        WHERE vr.direction = 'OUT' AND vr.pass_time BETWEEN ? AND ?
        GROUP BY day_date
        ORDER BY day_date ASC
    \"\"\", (start_str, end_str))"""
    
    new_analytics_daily_sql = """    cursor.execute(\"\"\"
        SELECT substr(vr.pass_time, 1, 10) as day_date,
               COUNT(*) as trips,
               SUM(COALESCE(st.unit_price, 0)) as cost
        FROM vehicle_records vr
        LEFT JOIN soil_types st ON vr.soil_type = st.name
        WHERE vr.direction = 'OUT' AND vr.pass_time BETWEEN ? AND ?
        GROUP BY day_date
        ORDER BY day_date ASC
    \"\"\", (start_str, end_str))"""
    
    code = code.replace(old_analytics_daily_sql, new_analytics_daily_sql)

    with open(server_path, "w", encoding="utf-8") as f:
        f.write(code)
        
    print("Backend update complete.")
    return True

def update_frontend():
    frontend_path = "templates/index.html"
    if not os.path.exists(frontend_path):
        print(f"Error: {frontend_path} not found.")
        return False
        
    with open(frontend_path, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. 在配置页 HTML 结构左侧列下部添加“土方类型单价价格配置”
    old_config_html = """                <span class="form-label" style="display:block; margin-bottom:8px; font-weight:700;">系统当前运行的对账场地名册</span>
                <div id="dump-sites-list-wrapper" style="flex-grow:1; overflow-y:auto; display:flex; flex-direction:column; gap:8px; padding-right:2px;">
                    <!-- 场地名册 -->
                </div>
            </div>"""
            
    new_config_html = """                <span class="form-label" style="display:block; margin-bottom:8px; font-weight:700;">系统当前运行的对账场地名册</span>
                <div id="dump-sites-list-wrapper" style="flex-grow:1; overflow-y:auto; display:flex; flex-direction:column; gap:8px; padding-right:2px; max-height:220px; border-bottom: 1px solid var(--card-border); margin-bottom: 16px; padding-bottom: 12px;">
                    <!-- 场地名册 -->
                </div>

                <!-- 增加：土方类型与单价管理配置 -->
                <div style="background:rgba(15, 23, 42, 0.02); border:1px solid var(--card-border); border-radius:8px; padding:12px; margin-bottom:16px;">
                    <span class="form-label" style="display:block; margin-bottom:8px; font-weight:700; color:var(--color-in);">添加新土方计价类型</span>
                    <div style="display:grid; grid-template-columns: 1fr 120px auto; gap:8px; align-items:flex-end;">
                        <div class="form-group" style="margin-bottom:0;">
                            <label class="form-label" for="new-soil-name">土方类型名称</label>
                            <input type="text" id="new-soil-name" placeholder="如 碎石" class="input-control">
                        </div>
                        <div class="form-group" style="margin-bottom:0;">
                            <label class="form-label" for="new-soil-price">结算单价(元/趟)</label>
                            <input type="number" id="new-soil-price" placeholder="如 120" class="input-control">
                        </div>
                        <button class="btn btn-accent" onclick="submitAddSoilType()" style="height:35px;">添加土方</button>
                    </div>
                </div>

                <span class="form-label" style="display:block; margin-bottom:8px; font-weight:700;">系统当前配置的土方单价名册</span>
                <div id="soil-types-list-wrapper" style="flex-grow:1; overflow-y:auto; display:flex; flex-direction:column; gap:8px; padding-right:2px; max-height:220px;">
                    <!-- 土方单价名册 -->
                </div>
            </div>"""
            
    html = html.replace(old_config_html, new_config_html)

    # 2. JavaScript 部分添加土方类型的全局变量与获取渲染逻辑
    old_globals = """        let currentFrequentPlatesList = [];
        let currentSitesList = [];"""
        
    new_globals = """        let currentFrequentPlatesList = [];
        let currentSitesList = [];
        let currentSoilsList = []; // 全局土方列表"""
        
    html = html.replace(old_globals, new_globals)

    # 3. 动态从 `/api/soil_types` 接口获取数据并渲染 dropdowns
    old_init = """        // Initialize
        refreshDumpSites()
        .then(() => {
            refreshFrequentPlates();
            switchTab('monitor');
        });"""
        
    new_init = """        // Initialize
        refreshDumpSites()
        .then(() => {
            return refreshSoilTypes();
        })
        .then(() => {
            refreshFrequentPlates();
            switchTab('monitor');
        });"""
        
    html = html.replace(old_init, new_init)

    # 4. 在 JS 中加入 refreshSoilTypes()、renderSoilTypesListConfig()、submitAddSoilType()、editSoilTypePrice()、submitDeleteSoilType()
    soil_js_logic = """
        // 获取与更新土方类型参数配置
        function refreshSoilTypes() {
            return fetch('/api/soil_types')
            .then(res => res.json())
            .then(data => {
                if (Array.isArray(data)) {
                    currentSoilsList = data;
                    syncSoilTypesDropdowns();
                }
            })
            .catch(err => console.error("加载土方列表失败:", err));
        }

        function syncSoilTypesDropdowns() {
            const manualSoilSelect = document.getElementById('manual-soil');
            if (manualSoilSelect) {
                let html = '';
                currentSoilsList.forEach(s => {
                    html += `<option value="${s.name}">${s.name} (￥${s.unit_price}/趟)</option>`;
                });
                manualSoilSelect.innerHTML = html;
            }
        }

        function submitAddSoilType() {
            const nameEl = document.getElementById('new-soil-name');
            const priceEl = document.getElementById('new-soil-price');
            const name = nameEl.value.trim();
            const price = parseFloat(priceEl.value);

            if (!name || isNaN(price) || price < 0) {
                showToast('输入错误', '请输入正确的土方名称和单价！', 'error');
                return;
            }

            fetch('/api/soil_types', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: name, unit_price: price })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast('土方类型添加成功', `已加入系统: ${name}`, 'success');
                    nameEl.value = '';
                    priceEl.value = '';
                    refreshSoilTypes().then(() => {
                        renderSoilTypesListConfig();
                    });
                } else {
                    showToast('添加失败', data.detail || '错误', 'error');
                }
            });
        }

        function editSoilTypePrice(id, name, currentPrice) {
            const newPriceStr = prompt(`请输入土方【${name}】的新结算单价（元/趟）：`, currentPrice);
            if (newPriceStr === null) return;
            const newPrice = parseFloat(newPriceStr);
            if (isNaN(newPrice) || newPrice < 0) {
                showToast('修改失败', '单价必须为有效数字！', 'error');
                return;
            }
            
            fetch(`/api/soil_types/${id}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: name, unit_price: newPrice })
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast('修改单价成功', `【${name}】的新单价为 ￥${newPrice}`, 'success');
                    refreshSoilTypes().then(() => {
                        renderSoilTypesListConfig();
                    });
                    if (currentTab === 'monitor') refreshDashboard();
                    if (currentTab === 'ledger') refreshLedger();
                } else {
                    showToast('修改失败', data.detail || '错误', 'error');
                }
            });
        }

        function submitDeleteSoilType(id, name) {
            if (!confirm(`确定要从系统移除土方类型【${name}】吗？删除后该类型的流水账目会自动被归结为默认土方类型。`)) return;
            fetch(`/api/soil_types/${id}`, { method: 'DELETE' })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showToast('土方删除成功', `已移除: ${name}`, 'success');
                    refreshSoilTypes().then(() => {
                        renderSoilTypesListConfig();
                    });
                }
            });
        }

        function renderSoilTypesListConfig() {
            const wrapper = document.getElementById('soil-types-list-wrapper');
            if (!wrapper) return;
            if (currentSoilsList.length === 0) {
                wrapper.innerHTML = `<div class="ranking-empty" style="padding: 20px 0;">当前系统未配置任何土方计价</div>`;
                return;
            }
            let html = '';
            currentSoilsList.forEach(s => {
                html += `
                    <div style="display:flex; justify-content:space-between; align-items:center; background:rgba(255,255,255,0.015); border:1px solid var(--card-border); border-radius:6px; padding:8px 12px;">
                        <div>
                            <span style="font-weight:700; color:var(--text-primary); font-size:13px;">${s.name}</span>
                            <span style="font-size:11px; color:var(--text-secondary); margin-left:8px;">计价单价: ￥${s.unit_price}/趟</span>
                        </div>
                        <div style="display:flex; gap:8px;">
                            <button class="btn btn-secondary" style="padding: 4px 10px; font-size:11px;" onclick="editSoilTypePrice(${s.id}, '${s.name}', ${s.unit_price})">
                                <i data-lucide="edit-3" style="width:12px; height:12px;"></i>修改单价
                            </button>
                            <button class="btn btn-danger" style="padding: 4px 10px; font-size:11px;" onclick="submitDeleteSoilType(${s.id}, '${s.name}')">
                                <i data-lucide="trash-2" style="width:12px; height:12px;"></i>删除
                            </button>
                        </div>
                    </div>
                `;
            });
            wrapper.innerHTML = html;
            lucide.createIcons({attrs: {"stroke-width": 2}});
        }
    """

    # 匹配在 renderDumpSitesListConfig 之后插入土方类型的 JS 函数
    html = html.replace("        function renderDumpSitesListConfig() {", soil_js_logic + "\n        function renderDumpSitesListConfig() {")

    # 5. 在 switchTab(tab) == 'config' 时，动态调用 renderSoilTypesListConfig()
    old_switch_config = """            } else if (tab === 'config') {
                if (headerTitle) headerTitle.innerText = "系统配置设置";
                if (headerIcon) headerIcon.setAttribute('data-lucide', 'settings');
                refreshDumpSites().then(() => {
                    renderDumpSitesListConfig();
                });
            }"""
            
    new_switch_config = """            } else if (tab === 'config') {
                if (headerTitle) headerTitle.innerText = "系统配置设置";
                if (headerIcon) headerIcon.setAttribute('data-lucide', 'settings');
                refreshDumpSites().then(() => {
                    renderDumpSitesListConfig();
                    renderSoilTypesListConfig(); // 渲染土方配置列表
                });
            }"""

    html = html.replace(old_switch_config, new_switch_config)

    # 6. 修改折线图提示框计算 (以土方计费为准)
    # 7. 修改 detailed ledger 表格单条费用计算 (基于土方单价)
    old_ledger_cost_calc = """                            const matchSite = currentSitesList.find(s => s.name === r.dump_site);
                            const unitPrice = matchSite ? matchSite.unit_price : 0.00;
                            const costVal = !isUnassigned ? unitPrice : 0.00;
                            const costText = isUnassigned ? '<span style="color:var(--color-danger); font-weight:700;">待分账</span>' : `￥${costVal.toFixed(2)}`;"""
                            
    new_ledger_cost_calc = """                            const matchSoil = currentSoilsList.find(s => s.name === r.soil_type);
                            const unitPrice = matchSoil ? matchSoil.unit_price : 0.00;
                            const costVal = !isUnassigned ? unitPrice : 0.00;
                            const costText = isUnassigned ? '<span style="color:var(--color-danger); font-weight:700;">待分账</span>' : `￥${costVal.toFixed(2)}`;"""

    html = html.replace(old_ledger_cost_calc, new_ledger_cost_calc)

    # 8. 修改 dashboard 通行明细费用计算 (基于土方单价)
    old_dashboard_cost_calc = """                        const matchSite = currentSitesList.find(s => s.name === r.dump_site);
                        const unitPrice = matchSite ? matchSite.unit_price : 0.00;
                        const costVal = !isUnassigned ? unitPrice : 0.00;
                        const costText = isUnassigned ? '<span style="color:var(--color-danger); font-weight:700;">待分账</span>' : `￥${costVal.toFixed(2)}`;"""
                        
    new_dashboard_cost_calc = """                        const matchSoil = currentSoilsList.find(s => s.name === r.soil_type);
                        const unitPrice = matchSoil ? matchSoil.unit_price : 0.00;
                        const costVal = !isUnassigned ? unitPrice : 0.00;
                        const costText = isUnassigned ? '<span style="color:var(--color-danger); font-weight:700;">待分账</span>' : `￥${costVal.toFixed(2)}`;"""

    html = html.replace(old_dashboard_cost_calc, new_dashboard_cost_calc)

    # 9. 修改 历史明细全日志弹窗 费用计算 (基于土方单价)
    old_modal_cost_calc = """                const matchSite = currentSitesList.find(s => s.name === r.dump_site);
                const unitPrice = matchSite ? matchSite.unit_price : 0.00;
                
                const isUnassigned = (r.dump_site === '未分配' || !r.dump_site);
                const costText = isUnassigned ? '<span style="color:var(--color-danger); font-weight:700;">待分账</span>' : '￥' + unitPrice.toFixed(2);"""
                
    new_modal_cost_calc = """                const matchSoil = currentSoilsList.find(s => s.name === r.soil_type);
                const unitPrice = matchSoil ? matchSoil.unit_price : 0.00;
                
                const isUnassigned = (r.dump_site === '未分配' || !r.dump_site);
                const costText = isUnassigned ? '<span style="color:var(--color-danger); font-weight:700;">待分账</span>' : '￥' + unitPrice.toFixed(2);"""

    html = html.replace(old_modal_cost_calc, new_modal_cost_calc)

    # 10. 在微调弹出窗口中，土方类型选择下拉菜单应该动态关联 `currentSoilsList`
    old_adjust_modal_soils = """                // 土质类型选择
                const soilType = r.soil_type || '渣土';
                const soilTypes = ["渣土", "好土", "二混子", "自卸", "级配石"];
                let soilSelectHtml = `<select class="input-control" style="width: 110px; padding: 4px 8px; font-size:12px; height: 30px;" onchange="submitSingleSoilAdjust(${r.id}, '${r.dump_site}', this.value)">`;
                soilTypes.forEach(st => {
                    soilSelectHtml += `<option value="${st}" ${soilType === st ? 'selected' : ''}>类型：${st}</option>`;
                });
                soilSelectHtml += `</select>`;"""
                
    new_adjust_modal_soils = """                // 土质类型选择
                const soilType = r.soil_type || '渣土';
                let soilSelectHtml = `<select class="input-control" style="width: 110px; padding: 4px 8px; font-size:12px; height: 30px;" onchange="submitSingleSoilAdjust(${r.id}, '${r.dump_site}', this.value)">`;
                currentSoilsList.forEach(st => {
                    soilSelectHtml += `<option value="${st.name}" ${soilType === st.name ? 'selected' : ''}>类型：${st.name}</option>`;
                });
                soilSelectHtml += `</select>`;"""

    html = html.replace(old_adjust_modal_soils, new_adjust_modal_soils)

    with open(frontend_path, "w", encoding="utf-8") as f:
        f.write(html)
        
    print("Frontend update complete.")
    return True

def main():
    if update_backend():
        update_frontend()
        print("Backend and Frontend updated successfully for custom soil prices!")

if __name__ == "__main__":
    main()

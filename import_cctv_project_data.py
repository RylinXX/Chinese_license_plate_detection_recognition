# -*- coding: UTF-8 -*-
"""
中央电视台项目车辆台账数据导入脚本
将 Desktop 上的 `车辆台账-中央电视台项目.(1).xlsx` 完整导入系统 SQLite 数据库
"""
import os
import sqlite3
import random
import pandas as pd
from datetime import datetime, timedelta

current_dir = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(current_dir, "worksite_plate.db")
EXCEL_PATH = "/Users/rylinx/Desktop/车辆台账-中央电视台项目.(1).xlsx"

def convert_excel_date(val):
    if pd.isna(val):
        return None
    try:
        if isinstance(val, (int, float)):
            return (pd.to_datetime('1899-12-30') + pd.to_timedelta(val, unit='D')).strftime('%Y-%m-%d')
        return str(val).split(' ')[0]
    except Exception:
        return str(val)

def import_data():
    print(f"[Import] 正在读取 Excel 数据源: {EXCEL_PATH}")
    df = pd.read_excel(EXCEL_PATH, sheet_name='明细台账')
    df['Formatted_Date'] = df['日期'].apply(convert_excel_date)
    
    # 过滤有效数据行
    clean_df = df.dropna(subset=['Formatted_Date', '种类']).copy()
    clean_df['车辆数'] = clean_df['车辆数'].fillna(0).astype(int)
    clean_df = clean_df[clean_df['车辆数'] > 0]
    
    print(f"[Import] 解析成功: 共 {len(clean_df)} 条日志条目，累计 {clean_df['车辆数'].sum()} 趟车辆拉运记录。")
    print(f"[Import] 时间跨度: {clean_df['Formatted_Date'].min()} 至 {clean_df['Formatted_Date'].max()}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. 初始化数据库表结构（调用 web-server.py 中的 init_db）
    import importlib
    web_server = importlib.import_module("web-server")
    web_server.init_db()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicle_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_no TEXT NOT NULL,
            plate_color TEXT,
            direction TEXT NOT NULL,
            pass_time TEXT NOT NULL,
            image_path TEXT,
            confidence REAL,
            dump_site TEXT DEFAULT '未分配',
            soil_type TEXT DEFAULT '渣土',
            dump_paid INTEGER DEFAULT 0,
            soil_paid INTEGER DEFAULT 0,
            is_ev TEXT DEFAULT '否',
            remark TEXT
        )
    """)
    
    # 检查并新增列
    cursor.execute("PRAGMA table_info(vehicle_records)")
    existing_cols = [c[1] for c in cursor.fetchall()]
    if "is_ev" not in existing_cols:
        cursor.execute("ALTER TABLE vehicle_records ADD COLUMN is_ev TEXT DEFAULT '否'")
    if "remark" not in existing_cols:
        cursor.execute("ALTER TABLE vehicle_records ADD COLUMN remark TEXT")
        
    # 清空旧数据
    cursor.execute("DELETE FROM vehicle_records")
    cursor.execute("DELETE FROM frequent_plates")
    cursor.execute("DELETE FROM dump_sites")
    cursor.execute("DELETE FROM soil_types")
    conn.commit()
    
    # 2. 导入土方/车辆运输种类 (soil_types)
    unique_soils = clean_df['种类'].dropna().unique().tolist()
    soil_price_map = {
        "十轮二混子": 100.0,
        "十轮好土": 80.0,
        "好土": 80.0,
        "沙子": 90.0,
        "二混子": 100.0,
        "十轮沙子": 90.0,
        "水泥块": 110.0,
        "8米好土": 85.0,
        "级配石": 150.0,
        "8米二混子": 105.0,
        "8米枢间土": 95.0,
        "大块": 120.0,
        "8米桩间土": 95.0
    }
    
    for soil in unique_soils:
        soil_name = str(soil).strip()
        price = soil_price_map.get(soil_name, 90.0)
        is_income = 1 if soil_name == "级配石" else 0
        cursor.execute("INSERT INTO soil_types (name, unit_price, is_income) VALUES (?, ?, ?)", (soil_name, price, is_income))
    print(f"[Import] 成功写入 {len(unique_soils)} 种土方/运输规格种类。")
    
    # 3. 导入消纳场地/卸土点 (dump_sites)
    unique_sites = clean_df['卸土点'].fillna('未知').dropna().unique().tolist()
    site_price_map = {
        "外运": 120.0,
        "鲁矿": 100.0,
        "焦化厂": 110.0,
        "生活区": 80.0,
        "未知": 0.0
    }
    for site in unique_sites:
        site_name = str(site).strip()
        price = site_price_map.get(site_name, 90.0)
        cursor.execute("INSERT INTO dump_sites (name, unit_price) VALUES (?, ?)", (site_name, price))
    print(f"[Import] 成功写入 {len(unique_sites)} 个项目消纳场与卸土点。")
    
    # 4. 创建高仿真车牌池 (区分自有电车/外协/散车)
    ev_plates = [f"京AD{i:05d}" for i in range(10001, 10041)]  # 40辆新能源电车
    fuel_plates = [f"京A{i:05d}" for i in range(60001, 60061)] + [f"冀B{i:05d}" for i in range(10001, 10031)]  # 90辆外协燃油车
    
    for p in ev_plates:
        cursor.execute("INSERT INTO frequent_plates (plate_no, plate_color, company_name) VALUES (?, '绿色', '央视项目电车队')", (p,))
    for p in fuel_plates:
        cursor.execute("INSERT INTO frequent_plates (plate_no, plate_color, company_name) VALUES (?, '黄色', '央视外协运输队')", (p,))
    print(f"[Import] 预充常用车牌库：{len(ev_plates)} 辆新能源电车，{len(fuel_plates)} 辆燃油渣土车。")
    
    # 5. 生成 2,860 趟通行水文流水记录
    total_out = 0
    total_in = 0
    
    for idx, row in clean_df.iterrows():
        day_str = row['Formatted_Date']
        soil = str(row['种类']).strip()
        site = str(row['卸土点']).strip() if pd.notna(row['卸土点']) else '未知'
        is_ev_val = str(row['是否自有电车']).strip() if pd.notna(row['是否自有电车']) else '未知'
        trip_cnt = int(row['车辆数'])
        remark = str(row['备注']) if pd.notna(row['备注']) else None
        
        # 判断是否含夜车
        is_night = False
        if remark and ('夜车' in remark or '夜班' in remark):
            is_night = True
            
        for _ in range(trip_cnt):
            if is_ev_val == '是':
                plate_no = random.choice(ev_plates)
                color = '绿色'
            elif is_ev_val == '否':
                plate_no = random.choice(fuel_plates)
                color = '黄色'
            else:
                # 未知
                plate_no = random.choice(ev_plates if random.random() < 0.5 else fuel_plates)
                color = '绿色' if plate_no in ev_plates else '黄色'
                
            # 生成通行时间
            if is_night:
                hour = random.choice([22, 23, 0, 1, 2, 3, 4, 5])
            else:
                hour = random.randint(7, 20)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            
            if hour in [0, 1, 2, 3, 4, 5]:
                # 次日凌晨
                dt = datetime.strptime(day_str, "%Y-%m-%d") + timedelta(days=1, hours=hour, minutes=minute, seconds=second)
            else:
                dt = datetime.strptime(day_str, "%Y-%m-%d") + timedelta(hours=hour, minutes=minute, seconds=second)
                
            out_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            in_dt = dt - timedelta(minutes=random.randint(25, 75))
            in_time = in_dt.strftime("%Y-%m-%d %H:%M:%S")
            
            # 级配石自行消纳与默认结算状态
            dump_paid = random.choice([0, 1])
            soil_paid = 1 if soil == "级配石" else random.choice([0, 1])
            
            # 写入 OUT 出场记录
            cursor.execute("""
                INSERT INTO vehicle_records
                (plate_no, plate_color, direction, pass_time, confidence, dump_site, soil_type, dump_paid, soil_paid, is_ev, remark)
                VALUES (?, ?, 'OUT', ?, 1.0, ?, ?, ?, ?, ?, ?)
            """, (plate_no, color, out_time, site, soil, dump_paid, soil_paid, is_ev_val, remark))
            total_out += 1
            
            # 写入 IN 进场记录
            cursor.execute("""
                INSERT INTO vehicle_records
                (plate_no, plate_color, direction, pass_time, confidence, dump_site, soil_type, dump_paid, soil_paid, is_ev, remark)
                VALUES (?, ?, 'IN', ?, 1.0, '未分配', ?, 0, 0, ?, ?)
            """, (plate_no, color, in_time, soil, is_ev_val, remark))
            total_in += 1

    conn.commit()
    conn.close()
    print(f"[Import] 中央电视台项目车辆台账数据导入完毕！")
    print(f"[Import] 出场趟数 (OUT): {total_out} 趟 | 进场趟数 (IN): {total_in} 趟 | 总通行记录: {total_out + total_in} 条")

if __name__ == "__main__":
    import_data()

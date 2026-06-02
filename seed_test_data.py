import sqlite3
import random
from datetime import datetime, timedelta

DB_PATH = r"C:\Users\RM\.gemini\antigravity\scratch\worksite_bookkeeping_app\worksite_plate.db"

def seed_demo_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 清空旧数据
    cursor.execute("DELETE FROM vehicle_records")
    cursor.execute("DELETE FROM frequent_plates")
    cursor.execute("DELETE FROM dump_sites")
    conn.commit()
    
    # 简化的土点名称
    dump_sites = [
        ("北山堆场", 120.0),
        ("东区填海", 150.0),
        ("南村洼地", 100.0),
        ("高新基坑", 130.0)
    ]
    
    for site, price in dump_sites:
        cursor.execute("INSERT INTO dump_sites (name, unit_price) VALUES (?, ?)", (site, price))
        
    # 车队与车辆 (每车队3-5辆车)
    fleets = {
        "豫林腾达": ["京A88888", "京A99999", "京A66666", "京A12345"],
        "顺丰基建": ["粤B11111", "粤B22222", "粤B33333"],
        "个人散车": ["冀C77777", "豫D88888"]
    }
    
    plates = []
    for fleet, fleet_plates in fleets.items():
        company = fleet if fleet != "个人散车" else ""
        for plate in fleet_plates:
            plates.append((plate, company))
            if company:
                cursor.execute("INSERT INTO frequent_plates (plate_no, company_name) VALUES (?, ?)", (plate, company))
                
    # 生成今天的流水记录 (50条)
    today_str = "2026-06-01"
    soil_types = ["渣土", "好土", "二混子", "级配石"]
    
    for i in range(50):
        plate, _ = random.choice(plates)
        site = random.choice(dump_sites)[0]
        soil = random.choice(soil_types)
        
        # 随机时间 08:00 到 18:00
        hour = random.randint(8, 17)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        pass_time = f"{today_str} {hour:02d}:{minute:02d}:{second:02d}"
        
        # 随机付款状态
        dump_paid = random.choice([0, 1])
        soil_paid = random.choice([0, 1])
        
        cursor.execute('''
            INSERT INTO vehicle_records 
            (plate_no, plate_color, direction, pass_time, dump_site, soil_type, dump_paid, soil_paid)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (plate, '黄色', 'OUT', pass_time, site, soil, dump_paid, soil_paid))
        
    conn.commit()
    conn.close()
    print("Demo data seeded successfully with simplified names.")

if __name__ == "__main__":
    seed_demo_data()

# -*- coding: UTF-8 -*-
import sqlite3
import random
from datetime import datetime, timedelta
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(current_dir, "worksite_plate.db")

def seed_seven_days():
    print("开始清空旧数据并重新初始化演示名册...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. 清空旧数据
    cursor.execute("DELETE FROM vehicle_records")
    cursor.execute("DELETE FROM frequent_plates")
    cursor.execute("DELETE FROM dump_sites")
    cursor.execute("DELETE FROM soil_types")
    conn.commit()
    
    # 2. 写入默认的消纳场
    dump_sites = [
        ("北山堆场", 120.0),
        ("东区填海", 150.0),
        ("南村洼地", 100.0),
        ("高新基坑", 130.0)
    ]
    for site, price in dump_sites:
        cursor.execute("INSERT INTO dump_sites (name, unit_price) VALUES (?, ?)", (site, price))
        
    # 3. 写入土方单价配置（含级配石收入属性）
    soil_types = [
        ("渣土", 60.0, 0),
        ("好土", 80.0, 0),
        ("二混子", 100.0, 0),
        ("自卸", 120.0, 0),
        ("级配石", 150.0, 1)
    ]
    for name, price, is_income in soil_types:
        cursor.execute("INSERT INTO soil_types (name, unit_price, is_income) VALUES (?, ?, ?)", (name, price, is_income))
        
    # 4. 车辆名册
    plates = [
        ("京A88888", "蓝色", "个人车主"),
        ("京A99999", "黄色", "老张车队"),
        ("京A66666", "黄色", "李总车队"),
        ("京A12345", "蓝色", "老王车队"),
        ("粤B11111", "蓝色", "散车车队"),
        ("粤B22222", "黄色", "刘老板车队"),
        ("粤B33333", "绿色", "散车车队"),
        ("冀C77777", "黄色", "赵自卸车队"),
        ("豫D88888", "黄色", "个人车主")
    ]
    for plate, color, company in plates:
        cursor.execute("INSERT INTO frequent_plates (plate_no, plate_color, company_name) VALUES (?, ?, ?)", (plate, color, company))
        
    # 5. 循环生成 7 天的数据（自 2026-05-27 至 2026-06-02，含今天）
    # 今天是 2026-06-02
    end_date = datetime(2026, 6, 2)
    start_date = end_date - timedelta(days=6)
    
    soil_names = [s[0] for s in soil_types]
    site_names = [d[0] for d in dump_sites]
    
    records_count = 0
    print(f"正在生成从 {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')} 的历史流水...")
    
    for day_offset in range(7):
        current_day = start_date + timedelta(days=day_offset)
        day_str = current_day.strftime("%Y-%m-%d")
        
        # 每天生成 20 到 30 条出场流水
        daily_trips = random.randint(20, 30)
        for _ in range(daily_trips):
            plate, color, _ = random.choice(plates)
            soil = random.choice(soil_names)
            
            if soil == "级配石":
                # 级配石自行消纳，没有常规消纳点
                site = "自行消纳"
                dump_paid = 1  # 自行消纳代表不需要对消纳账，故卸土费已结算
                soil_paid = random.choice([0, 1])  # 运费/售价是否收妥
            else:
                site = random.choice(site_names)
                dump_paid = random.choice([0, 1])
                soil_paid = random.choice([0, 1])
                
            # 通行时间 08:00 到 18:00
            hour = random.randint(8, 17)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            pass_time = f"{day_str} {hour:02d}:{minute:02d}:{second:02d}"
            
            # 写入出场记录
            cursor.execute("""
                INSERT INTO vehicle_records 
                (plate_no, plate_color, direction, pass_time, dump_site, soil_type, dump_paid, soil_paid, confidence)
                VALUES (?, ?, 'OUT', ?, ?, ?, ?, ?, 1.0)
            """, (plate, color, pass_time, site, soil, dump_paid, soil_paid))
            
            # 同时模拟对应的进场记录
            # 进场时间比出场早 30-90 分钟
            in_minutes = random.randint(30, 90)
            in_time_dt = datetime.strptime(pass_time, "%Y-%m-%d %H:%M:%S") - timedelta(minutes=in_minutes)
            in_pass_time = in_time_dt.strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute("""
                INSERT INTO vehicle_records 
                (plate_no, plate_color, direction, pass_time, dump_site, soil_type, dump_paid, soil_paid, confidence)
                VALUES (?, ?, 'IN', ?, '未分配', ?, 0, 0, 1.0)
            """, (plate, color, in_pass_time, soil))
            
            records_count += 2
            
    conn.commit()
    conn.close()
    print(f"7 days of high-fidelity seed data generated successfully! Total records: {records_count}")

if __name__ == "__main__":
    seed_seven_days()

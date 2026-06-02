import sqlite3
import urllib.request
import json
import random
from datetime import datetime

import os
current_dir = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(current_dir, "worksite_plate.db")
REGISTRY_URL = "https://web.rlxtc.com/api/public/vehicle-query"

def simplify_company_name(name):
    if not name or name == "None" or name == "个人车主":
        return "个人车主"
    
    # 移除省份城市名前缀
    for word in ["北京", "天津", "河北", "山西", "内蒙古", "辽宁", "吉林", "黑龙江", "上海", "江苏", "浙江", "安徽", "福建", "江西", "山东", "河南", "湖北", "湖南", "广东", "广西", "海南", "重庆", "四川", "贵州", "云南", "西藏", "陕西", "甘肃", "青海", "宁夏", "新疆"]:
        if name.startswith(word):
            name = name[len(word):]
            
    # 移除常见行业词
    for word in ["道路", "公路", "货物", "物流", "运输", "服务", "基建", "工程", "建筑", "建材", "商贸", "贸易", "科技", "新能源", "城建", "开发", "绿化", "市政", "渣土", "土石方", "环保", "物业", "管理"]:
        name = name.replace(word, "")
        
    # 移除常见后缀词
    for word in ["有限责任公司", "股份有限公司", "集团有限公司", "有限公司", "分公司", "办事处", "集团", "公司", "车队", "部"]:
        if name.endswith(word):
            name = name[:-len(word)]
        name = name.replace(word, "")
        
    name = name.strip()
    if not name:
        return "散车车队"
        
    # 截取前4个字符以确保极简 premium 外观 (3-5个字)
    if len(name) > 5:
        return name[:4]
    return name

def seed_real_vehicles():
    print("Fetching registered vehicles from external registry...")
    try:
        req = urllib.request.Request(REGISTRY_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error fetching vehicles: {e}")
        return
        
    vehicles = res_data.get("vehicles", [])
    if not vehicles:
        print("No vehicles parsed from external registry.")
        return
        
    print(f"Loaded {len(vehicles)} vehicles. Reseeding database...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. 清空原有流水和常用车辆名册
    cursor.execute("DELETE FROM vehicle_records")
    cursor.execute("DELETE FROM frequent_plates")
    cursor.execute("DELETE FROM dump_sites")
    cursor.execute("DELETE FROM soil_types")
    conn.commit()
    
    # 2. 插入简化的四大对账场地
    dump_sites = [
        ("北山堆场", 120.0),
        ("东区填海", 150.0),
        ("南村洼地", 100.0),
        ("高新基坑", 130.0)
    ]
    for name, price in dump_sites:
        cursor.execute("INSERT INTO dump_sites (name, unit_price) VALUES (?, ?)", (name, price))
        
    # 3. 插入简化的土方单价
    soil_types = [
        ("渣土", 80.0, 0),
        ("二混子", 100.0, 0),
        ("黄土", 120.0, 0),
        ("级配碎石", 160.0, 0)
    ]
    for s_name, price, is_income in soil_types:
        cursor.execute("INSERT INTO soil_types (name, unit_price, is_income) VALUES (?, ?, ?)", (s_name, price, is_income))
        
    # 4. 插入真实的常用车牌与精简车队名称
    FLEET_NAMES = [
        "老张车队",
        "李总车队",
        "老王车队",
        "刘老板车队",
        "陈总车队",
        "赵自卸车队",
        "马总车队",
        "小孙车队",
        "个人车主"
    ]
    inserted_plates = []
    for idx, v in enumerate(vehicles):
        plate_no = v.get("plate_no", "").upper().strip()
        if not plate_no:
            continue
        
        fleet = "个人车主"
            
        try:
            cursor.execute(
                "INSERT INTO frequent_plates (plate_no, plate_color, company_name) VALUES (?, ?, ?)",
                (plate_no, "黄色", fleet)
            )
            inserted_plates.append((plate_no, fleet))
        except sqlite3.IntegrityError:
            pass
            
    print(f"Successfully seeded {len(inserted_plates)} frequent plates.")
    
    # 5. 生成今日拉运高仿真数据 (50条流水)
    today_str = "2026-06-01"
    soil_names = [s[0] for s in soil_types]
    site_names = [d[0] for d in dump_sites]
    
    for i in range(50):
        # 随机挑选一个备案车牌
        plate_no, company = random.choice(inserted_plates)
        site = random.choice(site_names)
        soil = random.choice(soil_names)
        
        # 随机生成通行时间
        hour = random.randint(8, 18)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        pass_time = f"{today_str} {hour:02d}:{minute:02d}:{second:02d}"
        
        # 随机支付状态，级配石默认为已付 (1)
        dump_paid = random.choice([0, 1])
        soil_paid = 1 if soil == "级配石" else random.choice([0, 1])
        
        cursor.execute("""
            INSERT INTO vehicle_records 
            (plate_no, plate_color, direction, pass_time, dump_site, soil_type, dump_paid, soil_paid)
            VALUES (?, '黄色', 'OUT', ?, ?, ?, ?, ?)
        """, (plate_no, pass_time, site, soil, dump_paid, soil_paid))
        
    conn.commit()
    conn.close()
    print("Database seeding completed. 50 realistic OUT records generated.")

if __name__ == "__main__":
    seed_real_vehicles()

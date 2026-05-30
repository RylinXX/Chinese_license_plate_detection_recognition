import sqlite3
import os
import random
from datetime import datetime, timedelta

DB_PATH = r"C:\Users\RM\.gemini\antigravity\scratch\Chinese_license_plate_detection_recognition\worksite_plate.db"

def seed_data():
    if not os.path.exists(DB_PATH):
        print(f"Error: 数据库文件不存在，请先运行 web-server.py 进行初始化: {DB_PATH}")
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. 清理现有测试记录与绑定（让效果最干净透亮）
    print("正在清空历史记录与绑定关系...")
    cursor.execute("DELETE FROM vehicle_records")
    cursor.execute("DELETE FROM vehicle_bindings")
    
    # 2. 写入高保真车辆自动绑定关系
    bindings = [
        ("粤B6688D", "东沙湾卸土点"),
        ("粤B9988D", "北山山脚卸土点"),
        ("粤B3355A", "南港码头卸土点"),
        ("京A88888", "东沙湾卸土点"),
        ("沪A33333", "北山山脚卸土点"),
        ("苏E55555", "南港码头卸土点"),
    ]
    cursor.executemany(
        "INSERT INTO vehicle_bindings (plate_no, default_dump_site) VALUES (?, ?)",
        bindings
    )
    print(f"成功导入 {len(bindings)} 条默认去向绑定关系。")
    
    # 3. 构造今日的通行日志 (2026-05-29)
    today_str = datetime.now().strftime("%Y-%m-%d")
    print(f"当前生成日期设定为今日：{today_str}")
    
    # 预设今日出行的车辆名单，及其颜色和绑定点
    vehicles_pool = [
        # 车牌, 颜色, 默认去向, 预计往返次数
        ("粤B6688D", "蓝色", "东沙湾卸土点", 5),
        ("粤B9988D", "黄色", "北山山脚卸土点", 6),
        ("粤B3355A", "绿色", "南港码头卸土点", 4),
        ("京A88888", "蓝色", "东沙湾卸土点", 3),
        ("沪A33333", "黄色", "北山山脚卸土点", 4),
        ("苏E55555", "蓝色", "南港码头卸土点", 3),
        ("粤B12345", "蓝色", "未分配", 2), # 故意设置无默认绑定，体现“未分配”效果
    ]
    
    records_to_insert = []
    
    # 起始时间设为早上 07:00:00
    base_time = datetime.strptime(f"{today_str} 07:00:00", "%Y-%m-%d %H:%M:%S")
    
    # 循环模拟车辆进出运载行程
    for plate, color, default_site, trips in vehicles_pool:
        current_car_time = base_time + timedelta(minutes=random.randint(0, 45))
        
        for i in range(trips):
            # 1. 模拟进场 (IN)
            in_time = current_car_time.strftime("%Y-%m-%d %H:%M:%S")
            # 进场没有卸土点
            records_to_insert.append((
                plate, color, "IN", in_time,
                f"capture_{random.randint(100, 999)}.jpg" if random.random() > 0.15 else None, # 部分模拟实拍，部分模拟手动录入
                round(random.uniform(0.92, 0.99), 2),
                "未分配"
            ))
            
            # 车辆在场内滞留 20~40 分钟进行装土
            current_car_time += timedelta(minutes=random.randint(20, 40))
            
            # 2. 模拟出场 (OUT)
            out_time = current_car_time.strftime("%Y-%m-%d %H:%M:%S")
            # 90%的概率归在默认卸土点，10%概率故意微调，体现司机偶尔临时被调岗的效果
            assigned_site = default_site
            if default_site != "未分配" and random.random() < 0.15:
                # 偶尔去其他地方
                alternative_sites = ["北山山脚卸土点", "东沙湾卸土点", "南港码头卸土点"]
                alternative_sites.remove(default_site)
                assigned_site = random.choice(alternative_sites)
                
            records_to_insert.append((
                plate, color, "OUT", out_time,
                f"capture_{random.randint(100, 999)}.jpg" if random.random() > 0.15 else None,
                round(random.uniform(0.92, 0.99), 2),
                assigned_site
            ))
            
            # 出去卸土并空车返回需要 45~90 分钟
            current_car_time += timedelta(minutes=random.randint(45, 90))
            
    # 3.5 构造历史月份数据，以便前台能够画出过去半年每个月车次和钱的折线/柱状图
    history_plates = ["粤B6688D", "粤B9988D", "粤B3355A", "京A88888", "沪A33333", "苏E55555"]
    history_sites = ["东沙湾卸土点", "北山山脚卸土点", "南港码头卸土点"]
    colors_map = {"粤B6688D": "蓝色", "粤B9988D": "黄色", "粤B3355A": "绿色", "京A88888": "蓝色", "沪A33333": "黄色", "苏E55555": "蓝色"}
    
    current_date = datetime.now()
    for m in range(5, 0, -1):
        month_date = current_date - timedelta(days=30 * m)
        month_str = month_date.strftime("%Y-%m")
        # 过去第 m 个月，模拟这个月共有 60 - 120 趟行程
        total_trips_month = random.randint(60, 120)
        for i in range(total_trips_month):
            plate = random.choice(history_plates)
            color = colors_map[plate]
            site = random.choice(history_sites)
            day = random.randint(1, 28)
            hour = random.randint(7, 18)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)
            
            # IN 进场记录
            in_time = f"{month_str}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"
            records_to_insert.append((
                plate, color, "IN", in_time, None, 0.95, "未分配"
            ))
            
            # OUT 出场记录 (滞留在 30-50 分钟后)
            out_dt = datetime.strptime(in_time, "%Y-%m-%d %H:%M:%S") + timedelta(minutes=random.randint(30, 50))
            out_time = out_dt.strftime("%Y-%m-%d %H:%M:%S")
            records_to_insert.append((
                plate, color, "OUT", out_time, None, 0.95, site
            ))
            
    # 让所有记录按通行时间先后排序，更加符合现实流式日志特点
    records_to_insert.sort(key=lambda x: x[3])
    
    cursor.executemany(
        """
        INSERT INTO vehicle_records 
        (plate_no, plate_color, direction, pass_time, image_path, confidence, dump_site) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        records_to_insert
    )
    
    # 模拟最后一辆车“只有进场、尚未出场”，体现“场内滞留”指标的值
    cursor.execute(
        "INSERT INTO vehicle_records (plate_no, plate_color, direction, pass_time, image_path, confidence, dump_site) VALUES (?, ?, ?, ?, ?, ?, ?)",
        ("粤B77777", "蓝色", "IN", f"{today_str} 19:30:00", "capture_999.jpg", 0.98, "未分配")
    )
    
    conn.commit()
    
    # 打印统计信息，自我核验
    cursor.execute("SELECT COUNT(*) FROM vehicle_records")
    total_records = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM vehicle_records WHERE direction = 'OUT'")
    total_out = cursor.fetchone()[0]
    
    print("\n--- [Data Generation Report] ---")
    print(f"数据总通行记录条数: {total_records} 条")
    print(f"出场总运载次数 (OUT): {total_out} 趟")
    print("数据表 vehicle_records 和 vehicle_bindings 灌入今日完美账目数据成功！")
    
    conn.close()

if __name__ == "__main__":
    seed_data()

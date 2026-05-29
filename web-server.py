# -*- coding: UTF-8 -*-
from __future__ import annotations

import os
import sys
import uuid
import shutil
import sqlite3
import csv
from datetime import datetime, timedelta
from typing import Any

from fastapi import FastAPI, File, UploadFile, Query, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# 确保 recognizer 能被导入
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from recognizer import LocalSimulatedCloudRecognizer

app = FastAPI(title="工地车牌识别与进出统计后台系统")

# 基础路径配置
UPLOAD_DIR = os.path.join(current_dir, "uploaded_imgs")
DB_PATH = os.path.join(current_dir, "worksite_plate.db")
DEBOUNCE_SECONDS = 300  # 去重防抖时间（5分钟）

# 创建上传图片存储目录
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ----------------- 数据库初始化 -----------------
def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vehicle_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate_no TEXT NOT NULL,
            plate_color TEXT,
            direction TEXT NOT NULL, -- 'IN' 代表进场，'OUT' 代表出场
            pass_time TEXT NOT NULL,  -- YYYY-MM-DD HH:MM:SS 格式
            image_path TEXT,
            confidence REAL
        )
    """)
    conn.commit()
    conn.close()
    print("[Database] 数据库及数据表初始化成功。")

init_db()

# 初始化本地车牌识别引擎（模拟云端接口）
try:
    recognizer = LocalSimulatedCloudRecognizer(
        detect_model_path=os.path.join(current_dir, "weights", "plate_detect.pt"),
        rec_model_path=os.path.join(current_dir, "weights", "plate_rec_color.pth")
    )
except Exception as e:
    print(f"[Warning] 核心模型加载失败 (若为测试环境，请确保已下载权重): {e}")
    recognizer = None

# ----------------- 数据补录 Pydantic 结构 -----------------
class ManualImportRequest(BaseModel):
    plate_no: str
    plate_color: str = "蓝色"
    direction: str = "OUT"  # 'IN' / 'OUT'
    pass_time: str          # 格式 YYYY-MM-DD HH:MM:SS

# ----------------- 路由API实现 -----------------

@app.post("/api/manual_import")
async def manual_import_record(req: ManualImportRequest) -> dict[str, Any]:
    """
    允许管理员手动录入或补记历史通行数据（例如根据本子上的“正”字账目）。
    """
    if req.direction not in ("IN", "OUT"):
        raise HTTPException(status_code=400, detail="方向必须为 'IN' 或 'OUT'")
        
    plate_no = req.plate_no.upper().strip()
    if not plate_no:
        raise HTTPException(status_code=400, detail="车牌号不能为空")
        
    # 格式化验证通行时间
    try:
        datetime.strptime(req.pass_time, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise HTTPException(status_code=400, detail="时间格式不正确，必须为 YYYY-MM-DD HH:MM:SS")
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 写入数据库，image_path = None 代表人工手动补录，无抓拍照
    cursor.execute(
        "INSERT INTO vehicle_records (plate_no, plate_color, direction, pass_time, image_path, confidence) VALUES (?, ?, ?, ?, ?, ?)",
        (plate_no, req.plate_color, req.direction, req.pass_time, None, 1.0)
    )
    conn.commit()
    conn.close()
    
    print(f"[ManualImport] 人工成功补录通行记录: {plate_no} ({req.direction}) 时间: {req.pass_time}")
    
    return {
        "success": True,
        "message": f"成功人工补录车牌 {plate_no} 记录。"
    }

@app.post("/api/upload")
async def upload_vehicle_photo(
    file: UploadFile = File(...),
    direction: str = Query("OUT", description="进出方向：'IN' 代表进场，'OUT' 代表出场")
) -> dict[str, Any]:
    """
    接收工地摄像头抓拍并上传的图片，运行车牌识别，执行去重校验并记录。
    """
    if direction not in ("IN", "OUT"):
        raise HTTPException(status_code=400, detail="进出方向必须为 'IN' 或 'OUT'")
        
    # 保存图片文件
    file_ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    unique_filename = f"capture_{uuid.uuid4().hex[:12]}{file_ext}"
    saved_image_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    with open(saved_image_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    if recognizer is None:
        return {
            "success": False,
            "message": "车牌识别引擎加载失败，请联系管理员确认 weights/ 文件是否完整。"
        }
        
    try:
        # 调用车牌识别引擎
        results = recognizer.recognize(saved_image_path)
    except Exception as exc:
        # 出错时删除已保存图片
        if os.path.exists(saved_image_path):
            os.remove(saved_image_path)
        return {
            "success": False,
            "message": f"识别异常: {exc}"
        }
        
    if not results:
        # 如果未检测到车牌，保留大图以便人工核对，但不在主数据库写入记录
        return {
            "success": True,
            "detected": False,
            "message": "未检测到车牌信息",
            "results": []
        }
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    saved_records = []
    current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for plate in results:
        plate_no = plate["plate_no"]
        plate_color = plate["plate_color"]
        confidence = plate["recognition_confidence"]
        plate_type = plate["plate_type"]
        
        # ----------------- 去重防抖校验 -----------------
        # 查询该车牌最近一次通行记录
        cursor.execute(
            "SELECT id, pass_time, direction FROM vehicle_records WHERE plate_no = ? ORDER BY pass_time DESC LIMIT 1",
            (plate_no,)
        )
        last_record = cursor.fetchone()
        
        should_insert = True
        if last_record:
            record_id, last_time_str, last_direction = last_record
            last_time = datetime.strptime(last_time_str, "%Y-%m-%d %H:%M:%S")
            time_diff = (datetime.now() - last_time).total_seconds()
            
            # 若在设定去重时间范围内且方向一致，则视为相同通行事件，更新通行时间即可，不新增记录
            if time_diff < DEBOUNCE_SECONDS and last_direction == direction:
                should_insert = False
                cursor.execute(
                    "UPDATE vehicle_records SET pass_time = ?, image_path = ? WHERE id = ?",
                    (current_time_str, unique_filename, record_id)
                )
                print(f"[Debounce] 车牌 {plate_no} 重复触发，已更新最后通行时间。")
                saved_records.append({
                    "plate_no": plate_no,
                    "plate_color": plate_color,
                    "direction": direction,
                    "pass_time": current_time_str,
                    "status": "updated"
                })
                
        if should_insert:
            # 新增通行记录
            cursor.execute(
                "INSERT INTO vehicle_records (plate_no, plate_color, direction, pass_time, image_path, confidence) VALUES (?, ?, ?, ?, ?, ?)",
                (plate_no, plate_color, direction, current_time_str, unique_filename, confidence)
            )
            print(f"[Record] 成功写入车牌通行记录: {plate_no} ({direction})")
            saved_records.append({
                "plate_no": plate_no,
                "plate_color": plate_color,
                "direction": direction,
                "pass_time": current_time_str,
                "status": "inserted"
            })
            
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "detected": True,
        "results": saved_records
    }

@app.get("/api/records")
def get_records_by_date(
    date: str | None = Query(None, description="查询日期，格式 YYYY-MM-DD，默认今天"),
    limit: int = 100
) -> dict[str, Any]:
    """
    获取指定日期的通行记录列表、KPIs 统计指标以及各车辆的趟数汇总。
    """
    current_today = datetime.now().strftime("%Y-%m-%d")
    if not date:
        date = current_today
        
    query_start = f"{date} 00:00:00"
    query_end = f"{date} 23:59:59"
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 1. 查询该日所有通行记录
    cursor.execute(
        "SELECT id, plate_no, plate_color, direction, pass_time, image_path, confidence FROM vehicle_records WHERE pass_time BETWEEN ? AND ? ORDER BY pass_time DESC LIMIT ?",
        (query_start, query_end, limit)
    )
    rows = cursor.fetchall()
    
    records = []
    for r in rows:
        records.append({
            "id": r["id"],
            "plate_no": r["plate_no"],
            "plate_color": r["plate_color"],
            "direction": r["direction"],
            "pass_time": r["pass_time"],
            "image_url": f"/uploaded_imgs/{r['image_path']}" if r["image_path"] else None,
            "confidence": f"{r['confidence']:.2f}" if r["confidence"] else "1.00"
        })
        
    # 2. 统计该日进出总数
    cursor.execute(
        "SELECT COUNT(*) FROM vehicle_records WHERE direction = 'IN' AND pass_time BETWEEN ? AND ?",
        (query_start, query_end)
    )
    total_in = cursor.fetchone()[0]
    
    cursor.execute(
        "SELECT COUNT(*) FROM vehicle_records WHERE direction = 'OUT' AND pass_time BETWEEN ? AND ?",
        (query_start, query_end)
    )
    total_out = cursor.fetchone()[0]
    
    # 3. 统计当前场内滞留车辆 (此指标维持全系统最新的在场车数，不限日期，以保持其实时指导意义)
    cursor.execute("""
        WITH latest_records AS (
            SELECT plate_no, direction,
                   ROW_NUMBER() OVER(PARTITION BY plate_no ORDER BY pass_time DESC) as rn
            FROM vehicle_records
        )
        SELECT COUNT(*) FROM latest_records WHERE rn = 1 AND direction = 'IN'
    """)
    current_stay = cursor.fetchone()[0]
    
    # 4. 统计该日每辆车的进出趟数
    cursor.execute("""
        SELECT plate_no, plate_color,
               SUM(CASE WHEN direction = 'IN' THEN 1 ELSE 0 END) as in_cnt,
               SUM(CASE WHEN direction = 'OUT' THEN 1 ELSE 0 END) as out_cnt
        FROM vehicle_records
        WHERE pass_time BETWEEN ? AND ?
        GROUP BY plate_no
        ORDER BY out_cnt DESC, in_cnt DESC
    """, (query_start, query_end))
    
    trips = []
    for row in cursor.fetchall():
        trips.append({
            "plate_no": row["plate_no"],
            "plate_color": row["plate_color"] if row["plate_color"] else "未知",
            "in_cnt": row["in_cnt"],
            "out_cnt": row["out_cnt"],
            "total_trips": row["out_cnt"]
        })
        
    conn.close()
    
    return {
        "success": True,
        "selected_date": date,
        "is_today": date == current_today,
        "kpis": {
            "total_in": total_in,
            "total_out": total_out,
            "current_stay": current_stay
        },
        "records": records,
        "trips": trips
    }

@app.get("/api/export")
def export_records_to_csv(
    date: str | None = Query(None, description="要导出的日期，格式 YYYY-MM-DD，默认今天")
) -> StreamingResponse:
    """
    一键导出指定日期的全部通行数据为标准 CSV 表格文件。
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
        
    query_start = f"{date} 00:00:00"
    query_end = f"{date} 23:59:59"
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, plate_no, plate_color, direction, pass_time, confidence FROM vehicle_records WHERE pass_time BETWEEN ? AND ? ORDER BY pass_time DESC",
        (query_start, query_end)
    )
    rows = cursor.fetchall()
    conn.close()
    
    # 构造 CSV 数据流以防止占用内存
    def generate_csv_data() -> Any:
        import io
        output = io.StringIO()
        # 写入 UTF-8 BOM 以兼容 Excel 双击打开无乱码
        output.write('\ufeff')
        writer = csv.writer(output)
        writer.writerow(["记录编号", "车牌号码", "车牌颜色", "通行方向", "通行时间", "识别置信度"])
        
        for row in rows:
            record_id, plate_no, plate_color, direction, pass_time, conf = row
            dir_text = "进场 (IN)" if direction == "IN" else "出场 (OUT)"
            conf_val = f"{conf:.2f}" if conf else "1.00"
            writer.writerow([record_id, plate_no, plate_color, dir_text, pass_time, conf_val])
            
        yield output.getvalue()
        
    filename = f"worksite_records_{date}.csv"
    return StreamingResponse(
        generate_csv_data(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ----------------- 静态资源托管与主页面 -----------------

# 挂载上传图片目录，使得大屏页面可以渲染抓拍图片
app.mount("/uploaded_imgs", StaticFiles(directory=UPLOAD_DIR), name="uploaded_imgs")

# 主页大屏 HTML 渲染路由
@app.get("/", response_class=HTMLResponse)
def index_page() -> str:
    templates_dir = os.path.join(current_dir, "templates")
    html_path = os.path.join(templates_dir, "index.html")
    
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        raise HTTPException(status_code=404, detail="大屏前端 HTML 模板文件未找到，请确认 templates/index.html 存在。")

if __name__ == "__main__":
    import uvicorn
    # 启动后台服务，绑定所有 IP 地址以允许局域网内的网络摄像头或测试机接入
    uvicorn.run("web-server:app", host="127.0.0.1", port=8000, reload=True)

"""
database.py
-----------
โมดูลจัดการฐานข้อมูล SQLite แบบง่าย สำหรับระบบแจ้งเตือนการทานยาอัจฉริยะ

ทำไมถึงเลือก SQLite:
- เป็นไฟล์เดียว (medicines.db) ไม่ต้องติดตั้ง Database Server แยก
- ข้อมูลจะไม่หายเมื่อปิด/รีสตาร์ท Server เพราะข้อมูลถูกเขียนลงไฟล์จริงบนดิสก์
- เหมาะกับโปรเจกต์ขนาดเล็ก-กลาง และ Raspberry Pi ก็รันได้สบาย
"""

import sqlite3
import os
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "medicines.db")


def get_connection():
    """สร้าง connection ไปยังฐานข้อมูล พร้อมตั้งค่าให้ result เป็น dict-like (Row)"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """สร้างตาราง medicines ถ้ายังไม่มี (เรียกครั้งแรกตอน Server เริ่มทำงาน)"""
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS medicines (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT    NOT NULL,
            meal_timing     TEXT    NOT NULL,   -- ก่อนอาหาร / หลังอาหารทันที / หลังอาหาร / ก่อนนอน
            actual_time     TEXT    NOT NULL,   -- เวลาที่ต้องทานยาจริง HH:MM
            advance_minutes INTEGER NOT NULL DEFAULT 0,
            trigger_time    TEXT    NOT NULL,   -- เวลาที่คำนวณแล้ว HH:MM (actual_time - advance_minutes)
            image_filename  TEXT,
            is_active       INTEGER NOT NULL DEFAULT 1,  -- 1 = เปิดแจ้งเตือน, 0 = ปิดชั่วคราว
            created_at      TEXT    NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def calculate_trigger_time(actual_time: str, advance_minutes: int) -> str:
    """
    คำนวณ Trigger Time = actual_time - advance_minutes
    รองรับการข้ามเที่ยงคืน (เช่น ทาน 00:10 แจ้งล่วงหน้า 30 นาที -> ต้องได้ 23:40 ของวันก่อนหน้า)
    """
    base = datetime.strptime(actual_time, "%H:%M")
    trigger = base - timedelta(minutes=int(advance_minutes))
    return trigger.strftime("%H:%M")


def add_medicine(name, meal_timing, actual_time, advance_minutes, image_filename):
    trigger_time = calculate_trigger_time(actual_time, advance_minutes)
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO medicines
            (name, meal_timing, actual_time, advance_minutes, trigger_time, image_filename, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 1, ?)
        """,
        (
            name,
            meal_timing,
            actual_time,
            advance_minutes,
            trigger_time,
            image_filename,
            datetime.now().isoformat(timespec="seconds"),
        ),
    )
    conn.commit()
    conn.close()


def get_all_medicines():
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM medicines ORDER BY actual_time ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_medicine(med_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM medicines WHERE id = ?", (med_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def toggle_active(med_id):
    conn = get_connection()
    conn.execute(
        "UPDATE medicines SET is_active = 1 - is_active WHERE id = ?", (med_id,)
    )
    conn.commit()
    conn.close()


def delete_medicine(med_id):
    conn = get_connection()
    med = conn.execute(
        "SELECT image_filename FROM medicines WHERE id = ?", (med_id,)
    ).fetchone()
    conn.execute("DELETE FROM medicines WHERE id = ?", (med_id,))
    conn.commit()
    conn.close()
    return med["image_filename"] if med else None


def get_active_trigger_times():
    """คืนค่าเฉพาะ trigger_time ของยาที่ is_active = 1 เพื่อส่งให้บอร์ด Pico W"""
    conn = get_connection()
    rows = conn.execute(
        "SELECT trigger_time FROM medicines WHERE is_active = 1 ORDER BY trigger_time ASC"
    ).fetchall()
    conn.close()
    # ใช้ set กันเวลาซ้ำ แล้วค่อยเรียงกลับ
    return sorted({r["trigger_time"] for r in rows})

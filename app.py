"""
app.py
------
Web Server (Backend + Frontend) สำหรับระบบแจ้งเตือนการทานยาอัจฉริยะ
Smart Pill Reminder System

รันด้วยคำสั่ง:
    python app.py

จากนั้นเปิดเบราว์เซอร์ไปที่ http://127.0.0.1:5000
(ถ้าจะให้ Pico W ในวง Wi-Fi เดียวกันเรียกได้ ให้ดู IP เครื่องนี้แล้วใช้ IP นั้นแทน 127.0.0.1)
"""

import os
import uuid
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    flash,
)
from werkzeug.utils import secure_filename

import database as db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB

MEAL_TIMING_OPTIONS = [
    "ก่อนอาหาร",
    "หลังอาหารทันที",
    "หลังอาหาร",
    "ก่อนนอน",
]

app = Flask(__name__)
app.secret_key = "smart-pill-reminder-secret-key"  # เปลี่ยนเป็นค่าสุ่มจริงเมื่อ deploy
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------------------------------------------------------------------------
# หน้าเว็บ (Frontend)
# ---------------------------------------------------------------------------

@app.route("/")
def dashboard():
    """หน้า Dashboard หลัก: ฟอร์มเพิ่มยา + รายการยาทั้งหมด"""
    medicines = db.get_all_medicines()
    return render_template(
        "index.html",
        medicines=medicines,
        meal_options=MEAL_TIMING_OPTIONS,
    )


@app.route("/add", methods=["POST"])
def add_medicine():
    name = request.form.get("name", "").strip()
    meal_timing = request.form.get("meal_timing", "").strip()
    actual_time = request.form.get("actual_time", "").strip()
    advance_minutes = request.form.get("advance_minutes", "0").strip()

    # --- validation ฝั่ง server (กันข้อมูลผิดพลาด แม้ฟอร์มฝั่ง client จะเช็คแล้ว) ---
    if not name or not meal_timing or not actual_time:
        flash("กรุณากรอกข้อมูลให้ครบถ้วน (ชื่อยา, มื้อยา, เวลาที่ต้องทาน)", "error")
        return redirect(url_for("dashboard"))

    try:
        advance_minutes = int(advance_minutes) if advance_minutes else 0
        if advance_minutes < 0:
            raise ValueError
    except ValueError:
        flash("เวลาแจ้งเตือนล่วงหน้าต้องเป็นตัวเลขจำนวนเต็มไม่ติดลบ", "error")
        return redirect(url_for("dashboard"))

    # --- จัดการไฟล์รูปภาพ (ไม่บังคับ) ---
    image_filename = None
    file = request.files.get("image")
    if file and file.filename:
        if not allowed_file(file.filename):
            flash("รองรับเฉพาะไฟล์รูปภาพ (.png .jpg .jpeg .gif .webp) เท่านั้น", "error")
            return redirect(url_for("dashboard"))
        ext = file.filename.rsplit(".", 1)[1].lower()
        image_filename = f"{uuid.uuid4().hex}.{ext}"
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(image_filename)))

    db.add_medicine(name, meal_timing, actual_time, advance_minutes, image_filename)
    flash(f'เพิ่มยา "{name}" เรียบร้อยแล้ว', "success")
    return redirect(url_for("dashboard"))


@app.route("/toggle/<int:med_id>", methods=["POST"])
def toggle_medicine(med_id):
    """เปิด/ปิดการแจ้งเตือนของยารายการนั้นชั่วคราว โดยไม่ต้องลบทิ้ง"""
    db.toggle_active(med_id)
    return redirect(url_for("dashboard"))


@app.route("/delete/<int:med_id>", methods=["POST"])
def delete_medicine(med_id):
    image_filename = db.delete_medicine(med_id)
    if image_filename:
        path = os.path.join(app.config["UPLOAD_FOLDER"], image_filename)
        if os.path.exists(path):
            os.remove(path)
    flash("ลบรายการยาเรียบร้อยแล้ว", "success")
    return redirect(url_for("dashboard"))


# ---------------------------------------------------------------------------
# API สำหรับบอร์ดฮาร์ดแวร์ (Raspberry Pi Pico W) มาดึงข้อมูล
# ---------------------------------------------------------------------------

@app.route("/api/trigger-times", methods=["GET"])
def api_trigger_times():
    """
    คืนค่า JSON list ของเวลาที่ต้องแจ้งเตือน (เฉพาะยาที่เปิดใช้งานอยู่)
    ตัวอย่าง response: ["08:00", "12:15", "20:00"]
    บอร์ด Pico W จะเรียก endpoint นี้ทุก 1 นาที
    """
    trigger_times = db.get_active_trigger_times()
    return jsonify(trigger_times)


@app.route("/api/medicines", methods=["GET"])
def api_medicines():
    """(bonus) คืนรายละเอียดยาทั้งหมดแบบเต็ม เผื่อนำไปทำหน้าจออื่น หรือ debug"""
    return jsonify(db.get_all_medicines())


if __name__ == "__main__":
    db.init_db()
    # host="0.0.0.0" ทำให้อุปกรณ์อื่นในวง Wi-Fi เดียวกัน (เช่น Pico W) เรียก API มาได้
    app.run(host="0.0.0.0", port=5000, debug=True)

# 💊 Smart Pill Reminder — ระบบแจ้งเตือนการทานยาอัจฉริยะ

สถาปัตยกรรมแบบ **Decoupled**: Web Server (Flask + SQLite) ทำหน้าที่เก็บ/จัดการข้อมูล
ส่วน Raspberry Pi Pico W (MicroPython) ทำหน้าที่ดึงข้อมูลผ่าน HTTP API แล้วสั่งเสียง Buzzer เตือน

```
smart_pill_reminder/
├── app.py                 # Flask app: routes, upload รูป, API endpoint
├── database.py             # จัดการ SQLite (CRUD + คำนวณ trigger time)
├── requirements.txt
├── database/
│   └── medicines.db        # ไฟล์ฐานข้อมูล (สร้างอัตโนมัติตอนรันครั้งแรก)
├── static/
│   ├── css/style.css
│   ├── js/script.js         # preview รูปก่อนอัปโหลด
│   └── uploads/             # เก็บรูปซองยา/เม็ดยาที่อัปโหลด
├── templates/
│   ├── base.html            # layout, Tailwind, ฟอนต์ Kanit
│   └── index.html           # ฟอร์มเพิ่มยา + Dashboard
└── pico/                    # โค้ดที่ต้องอัปโหลดขึ้นบอร์ด Pico W
    ├── config.py             # ตั้งค่า Wi-Fi / IP server / พิน buzzer
    └── main.py               # main loop: NTP, HTTP GET ทุก 1 นาที, สั่ง buzzer
```

---

## 1) วิธีรัน Web Server

```bash
cd smart_pill_reminder
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

เปิดเบราว์เซอร์ไปที่ **http://127.0.0.1:5000**

ฐานข้อมูล SQLite (`database/medicines.db`) จะถูกสร้างอัตโนมัติตอนรันครั้งแรก
และข้อมูลจะยังอยู่ครบแม้ปิด/เปิด Server ใหม่ เพราะเก็บลงไฟล์จริงบนดิสก์ ไม่ใช่ในหน่วยความจำ

**สำคัญ:** ให้เครื่องที่รัน Server อยู่ใน Wi-Fi วงเดียวกับ Pico W แล้วดู IP ของเครื่อง
(`ipconfig` บน Windows หรือ `ifconfig`/`ip addr` บน Mac/Linux) เพื่อนำไปใส่ใน `pico/config.py`

---

## 2) วิธีอัปโหลดโค้ดขึ้น Raspberry Pi Pico W

1. ติดตั้ง [Thonny IDE](https://thonny.org/) แล้วเลือก Interpreter เป็น **MicroPython (Raspberry Pi Pico)**
2. ติดตั้งไลบรารี `urequests` บนบอร์ด (เปิด Shell ใน Thonny แล้วรัน):
   ```python
   import mip
   mip.install("urequests")
   ```
3. แก้ค่าใน `pico/config.py`:
   - `WIFI_SSID`, `WIFI_PASSWORD`
   - `API_BASE_URL` → ใส่ IP ของเครื่องที่รัน Flask (เช่น `http://192.168.1.100:5000`)
4. อัปโหลดไฟล์ `config.py` และ `main.py` ขึ้นบอร์ด (Save as... เลือก Raspberry Pi Pico)
   ตั้งชื่อไฟล์เป็น `main.py` เพื่อให้รันอัตโนมัติทุกครั้งที่เสียบไฟ
5. ต่อขา **Active Buzzer** เข้ากับ **GP15** และ **GND**

---

## 3) การทำงานของระบบ

1. ผู้ใช้กรอกฟอร์มบนเว็บ → เลือกมื้อยา, เวลาที่ต้องทานจริง, เวลาแจ้งเตือนล่วงหน้า, แนบรูป
2. Server คำนวณ **Trigger Time = เวลาที่ต้องทานจริง − เวลาแจ้งเตือนล่วงหน้า** แล้วบันทึกลง SQLite
3. Pico W เชื่อม Wi-Fi → ซิงค์เวลาแม่นยำผ่าน NTP → แปลงเป็นเวลาไทย (GMT+7)
4. ทุก 60 วินาที Pico W ยิง `GET /api/trigger-times` เพื่อดึงตารางล่าสุด เช่น `["08:00", "12:15", "20:00"]`
5. Pico W เทียบเวลาปัจจุบัน (HH:MM) กับตาราง ถ้าตรง → สั่ง Buzzer ที่ GP15 ดังรัว ๆ เตือนกินยา

---

## 4) ทดสอบ API ด้วยตัวเอง

```bash
curl http://127.0.0.1:5000/api/trigger-times
# -> ["08:00", "12:15", "20:00"]
```

---

## 5) จะรัน/โฮสต์โปรเจกต์นี้ที่ไหนได้บ้าง

| ตัวเลือก | เหมาะกับ | หมายเหตุ |
|---|---|---|
| **รันบน PC/Notebook ธรรมดา** ในบ้าน (`python app.py`) | ทดสอบ/ใช้งานจริงในบ้าน | ง่ายสุด แต่ต้องเปิดเครื่องทิ้งไว้ และ Pico W ต้องอยู่ Wi-Fi วงเดียวกัน |
| **รันบน Raspberry Pi (ตัวแยก) ในบ้าน** | อยากให้ทำงาน 24 ชม. โดยไม่ง้อ PC | ใช้ไฟน้อย เปิดทิ้งไว้ได้ตลอด เหมาะกับโปรเจกต์นี้มาก |
| **Deploy ขึ้นคลาวด์ฟรี** เช่น Render, Railway, PythonAnywhere | อยากเข้าถึง Dashboard จากนอกบ้าน/มือถือได้ | ต้องแก้ `config.py` ของ Pico ให้ชี้ไป URL คลาวด์แทน IP ในบ้าน และเปลี่ยนจาก SQLite ไฟล์เดียวเป็นแบบ persistent disk (Render มี Persistent Disk ให้เพิ่มได้) |
| **Docker container** | อยากให้ deploy ซ้ำง่าย/ย้ายเครื่องง่าย | เขียน Dockerfile ครอบ `app.py` ได้เลย ถ้าต้องการแจ้งมาเพิ่มได้ |

ถ้าจะให้ใช้งานง่ายและเสถียรที่สุดสำหรับโปรเจกต์ IoT แบบนี้ แนะนำ **รันบน Raspberry Pi (หรือ mini PC) เครื่องเล็ก ๆ เปิดทิ้งไว้ในบ้านตลอด** เพราะ Pico W ต้องยิง request เข้ามาทุกนาที ให้ Server พร้อมตอบตลอดเวลาจะดีที่สุด — ถ้าอยากได้ทั้งแบบ deploy คลาวด์ด้วย บอกได้ ผมเตรียม Dockerfile หรือ config ให้เพิ่มได้ครับ

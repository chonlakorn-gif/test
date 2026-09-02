# config.py
# ----------
# แก้ค่าตรงนี้ให้ตรงกับ Wi-Fi และ Web Server ของคุณ
# แล้วอัปโหลดไฟล์นี้คู่กับ main.py ขึ้นบอร์ด Raspberry Pi Pico W

WIFI_SSID = "YOUR_WIFI_SSID"
WIFI_PASSWORD = "YOUR_WIFI_PASSWORD"

# IP ของเครื่องที่รัน Flask server (ต้องอยู่วง Wi-Fi/เครือข่ายเดียวกับ Pico W)
# หาได้จากคำสั่ง:  ipconfig (Windows)  หรือ  ifconfig / ip addr (Mac/Linux)
API_BASE_URL = "http://192.168.1.100:5000"
TRIGGER_TIME_ENDPOINT = API_BASE_URL + "/api/trigger-times"

BUZZER_PIN = 15          # GP15 ต่อกับ Active Buzzer
FETCH_INTERVAL_SEC = 60  # ดึงข้อมูลตารางยาใหม่ทุก 60 วินาที
TIMEZONE_OFFSET_HOURS = 7  # ประเทศไทย GMT+7

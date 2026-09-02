# main.py
# -------
# Smart Pill Reminder — ฝั่งฮาร์ดแวร์ (Raspberry Pi Pico W, MicroPython)
#
# หน้าที่ของโค้ดนี้:
#   1. เชื่อมต่อ Wi-Fi
#   2. ตั้งเวลาให้ถูกต้องผ่าน NTP แล้วปรับเป็นเวลาไทย (GMT+7)
#   3. ทุก ๆ 60 วินาที: ยิง HTTP GET ไปที่ Web Server เพื่อดึงตาราง Trigger Time ล่าสุด
#   4. เทียบเวลาปัจจุบัน (HH:MM) กับตาราง ถ้าตรง -> สั่ง Buzzer (GP15) ดังรัว ๆ เพื่อเตือนกินยา
#
# ไลบรารีที่ต้องติดตั้งเพิ่มบนบอร์ด (ผ่าน Thonny -> Tools -> Manage Packages หรือ mip):
#   import mip
#   mip.install("urequests")

import network
import ntptime
import utime
import machine
import urequests
import time

from config import (
    WIFI_SSID,
    WIFI_PASSWORD,
    TRIGGER_TIME_ENDPOINT,
    BUZZER_PIN,
    FETCH_INTERVAL_SEC,
    TIMEZONE_OFFSET_HOURS,
)

buzzer = machine.Pin(BUZZER_PIN, machine.Pin.OUT)
buzzer.value(0)

# เก็บลิสต์เวลาแจ้งเตือนล่าสุดที่ดึงมาจาก Server เช่น ["08:00", "12:15", "20:00"]
trigger_times = []

# กันไม่ให้ buzzer ดังซ้ำหลายรอบในนาทีเดียวกัน (เก็บ "HH:MM" ล่าสุดที่เพิ่งเตือนไปแล้ว)
last_triggered_minute = ""


def connect_wifi():
    """เชื่อมต่อ Wi-Fi และรอจนกว่าจะสำเร็จ"""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("กำลังเชื่อมต่อ Wi-Fi: {}".format(WIFI_SSID))
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        timeout = 20
        while not wlan.isconnected() and timeout > 0:
            print(".", end="")
            utime.sleep(1)
            timeout -= 1
        print()

    if wlan.isconnected():
        print("เชื่อมต่อ Wi-Fi สำเร็จ! IP:", wlan.ifconfig()[0])
        return True
    else:
        print("เชื่อมต่อ Wi-Fi ไม่สำเร็จ")
        return False


def sync_time():
    """ดึงเวลาแม่นยำจาก NTP server (เวลาที่ได้เป็น UTC)"""
    try:
        ntptime.settime()
        print("ซิงค์เวลา NTP สำเร็จ (UTC)")
        return True
    except Exception as e:
        print("ซิงค์เวลา NTP ไม่สำเร็จ:", e)
        return False


def get_thailand_time():
    """
    คืนค่า (hour, minute) เป็นเวลาประเทศไทย (GMT+7)
    RTC ของ Pico เก็บเป็น UTC เสมอหลัง ntptime.settime() ดังนั้นต้อง +7 ชั่วโมงเอง
    """
    utc_now = utime.time()  # epoch seconds (UTC)
    local_now = utc_now + TIMEZONE_OFFSET_HOURS * 3600
    time_tuple = utime.localtime(local_now)
    # utime.localtime -> (year, month, mday, hour, minute, second, weekday, yearday)
    hour = time_tuple[3]
    minute = time_tuple[4]
    return hour, minute


def fetch_trigger_times():
    """เรียก API ของ Web Server เพื่อดึงตาราง Trigger Time ล่าสุด"""
    global trigger_times
    try:
        response = urequests.get(TRIGGER_TIME_ENDPOINT, timeout=10)
        if response.status_code == 200:
            trigger_times = response.json()
            print("อัปเดตตารางแจ้งเตือน:", trigger_times)
        else:
            print("Server ตอบกลับสถานะ:", response.status_code)
        response.close()
    except Exception as e:
        print("ดึงข้อมูลจาก API ไม่สำเร็จ:", e)


def sound_alarm():
    """สั่งให้ Active Buzzer ส่งเสียงเตือนรัว ๆ"""
    print("!!! ถึงเวลาทานยา -> ดังเตือน !!!")
    for _ in range(10):
        buzzer.value(1)
        utime.sleep(0.2)
        buzzer.value(0)
        utime.sleep(0.2)


def main():
    global last_triggered_minute

    if not connect_wifi():
        # ถ้าต่อ Wi-Fi ไม่ได้ ให้ลองใหม่เรื่อย ๆ ทุก 10 วินาที
        while not connect_wifi():
            utime.sleep(10)

    sync_time()
    fetch_trigger_times()

    last_fetch = time.time()

    while True:
        # --- ดึงตารางเวลาใหม่ทุก FETCH_INTERVAL_SEC วินาที ---
        if time.time() - last_fetch >= FETCH_INTERVAL_SEC:
            if not network.WLAN(network.STA_IF).isconnected():
                connect_wifi()
            fetch_trigger_times()
            last_fetch = time.time()

        # --- เช็คเวลาปัจจุบันเทียบกับตาราง ---
        hour, minute = get_thailand_time()
        current_hm = "{:02d}:{:02d}".format(hour, minute)

        if current_hm in trigger_times and current_hm != last_triggered_minute:
            sound_alarm()
            last_triggered_minute = current_hm

        utime.sleep(1)  # เช็คทุก 1 วินาที เพื่อความแม่นยำในการจับจังหวะนาทีที่เปลี่ยน


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
STeaMi Motion Lab - serveur BLE GATT (MVP)
==========================================
Diffuse les mesures VL53L1X (distance) + ISM330DLC (accelerometre + gyroscope)
vers un smartphone via Bluetooth Low Energy.

Trame NOTIFY (CSV, UTF-8), par exemple a 20 Hz :
    T,dist,ax,ay,az,gx,gy,gz
    T      : ms depuis le demarrage de l'acquisition (uint)
    dist   : mm (int, -1 si hors portee / erreur ToF)
    ax..az : acceleration en g        (float)
    gx..gz : rotation en deg/s        (float)

Caracteristiques GATT :
    SERVICE  a9e6f000-5b8c-4f4a-8b3a-1c2d3e4f5a6b
    DATA    a9e6f001-5b8c-4f4a-8b3a-1c2d3e4f5a6b  (read + notify) -> la trame ci-dessus
    CMD     a9e6f002-5b8c-4f4a-8b3a-1c2d3e4f5a6b  (write)         -> "START"/"STOP"/"RESET"
    STATUS  a9e6f003-5b8c-4f4a-8b3a-1c2d3e4f5a6b  (read + notify) -> "IDLE" / "RUN"

Nom BT : STeaMi-Motion

Deploiement : copier ce fichier vers main.py sur la carte
    mpremote connect <port> cp motion_lab_server.py :main.py
"""

import time
from micropython import const
from machine import I2C, Pin, SPI
import bluetooth
from bluetooth import BLE, UUID

try:
    from ism330dl import ISM330DL
    from vl53l1x import VL53L1X
except Exception as e:
    print("driver import error:", e)
    raise

# OLED rond optionnel : le serveur tourne aussi sans ecran (headless)
try:
    import ssd1327
    _HAVE_OLED = True
except Exception:
    _HAVE_OLED = False

# ---------------- parametres ----------------
_SAMPLE_MS = 50            # 20 Hz
_ADV_MS = 20000
_NAME = b"STeaMi-Motion"

_SVC = UUID("a9e6f000-5b8c-4f4a-8b3a-1c2d3e4f5a6b")
_DATA = UUID("a9e6f001-5b8c-4f4a-8b3a-1c2d3e4f5a6b")
_CMD = UUID("a9e6f002-5b8c-4f4a-8b3a-1c2d3e4f5a6b")
_STAT = UUID("a9e6f003-5b8c-4f4a-8b3a-1c2d3e4f5a6b")

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

# ---------------- hardware ----------------
i2c = I2C(1)
imu = ISM330DL(i2c)
dist = VL53L1X(i2c)
dist.start_ranging()

fb = None
raw = None
if _HAVE_OLED:
    try:
        spi = SPI(1)
        raw = ssd1327.WS_OLED_128X128_SPI(
            spi, Pin("DATA_COMMAND_DISPLAY"),
            Pin("RST_DISPLAY"), Pin("CS_DISPLAY"))
        fb = raw.framebuf
    except Exception:
        fb = None

ble = BLE()
ble.active(1)
_connh = None
_cmd_handle = None
_data_handle = None
_status_handle = None
_running = False
_t0 = 0
_notif = 0


def _irq(event, data):
    global _connh, _running, _cmd_handle
    if event == _IRQ_CENTRAL_CONNECT:
        _connh, _, _ = data
    elif event == _IRQ_CENTRAL_DISCONNECT:
        _connh = None
        _running = False
        _set_status("IDLE")
        ble.gap_advertise(20000, adv, resp_data=resp)
    elif event == _IRQ_GATTS_WRITE:
        conn, h = data[0], data[1]
        if h == _cmd_handle:
            try:
                val = ble.gatts_read(h).decode().strip().upper()
            except Exception:
                val = ""
            _handle_cmd(val)


def _handle_cmd(cmd):
    global _running, _t0
    if cmd == "START":
        _running = True
        _t0 = time.ticks_ms()
        _set_status("RUN")
    elif cmd == "STOP":
        _running = False
        _set_status("IDLE")
    elif cmd == "RESET":
        _running = False
        _t0 = 0
        _set_status("IDLE")


def _set_status(s):
    try:
        ble.gatts_write(_status_handle, s.encode())
        if _connh is not None:
            ble.gatts_notify(_connh, _status_handle, s.encode())
    except Exception:
        pass


def read_sensors():
    ax, ay, az = imu.acceleration_g()
    gx, gy, gz = imu.gyroscope_dps()
    try:
        d = dist.read()
    except Exception:
        d = -1
    return d, ax, ay, az, gx, gy, gz


def draw(vals, status):
    if fb is None or raw is None:
        return
    d, ax, ay, az, gx, gy, gz = vals
    fb.fill(0)
    lines = [
        ("STeaMi Motion", 15),
        (status, 9),
        ("D %d mm" % d, 9),
        ("A %.2f %.2f %.2f" % (ax, ay, az), 9),
        ("G %.1f %.1f %.1f" % (gx, gy, gz), 9),
        ("N %d" % _notif, 9),
    ]
    yy = 18
    for ln, col in lines:
        x = max(0, 64 - len(ln) * 4)
        fb.text(ln, x, yy, col)
        yy += 18
    raw.show()


# ---------------- GATT ----------------
srv = (_SVC, (
    (_DATA, bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY),
    (_CMD, bluetooth.FLAG_WRITE),
    (_STAT, bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY),
))
(_data_handle, _cmd_handle, _status_handle) = ble.gatts_register_services((srv,))[0]

_UUID_STR = "a9e6f000-5b8c-4f4a-8b3a-1c2d3e4f5a6b"
_le = bytes(reversed(bytes.fromhex(_UUID_STR.replace("-", ""))))
# Advertising data is limited to 31 bytes. Keep it short here
# (flags + 128-bit service UUID = 21 bytes) and put the full name
# in the scan response so the Android picker still shows a clear label.
adv = b"\x02\x01\x06" + b"\x11\x07" + _le
resp = bytes([len(_NAME) + 1, 0x09]) + _NAME

ble.irq(_irq)
ble.gatts_write(_status_handle, b"IDLE")
ble.gap_advertise(_ADV_MS, adv, resp_data=resp)
print("STeaMi Motion Lab - serveur BLE en attente de connexion")

draw((0, 0, 0, 0, 0, 0, 0), "IDLE")

n = 0
try:
    while True:
        if _running and _connh is not None:
            d, ax, ay, az, gx, gy, gz = read_sensors()
            t = time.ticks_ms() - _t0
            s = "%d,%d,%.3f,%.3f,%.3f,%.2f,%.2f,%.2f" % (t, d, ax, ay, az, gx, gy, gz)
            b = s.encode()
            ble.gatts_write(_data_handle, b)
            try:
                ble.gatts_notify(_connh, _data_handle, b)
                _notif += 1
            except Exception:
                pass
            draw((d, ax, ay, az, gx, gy, gz), "RUN")
            if n % 20 == 0:
                print("sample:", s)
            n += 1
        else:
            time.sleep_ms(_SAMPLE_MS)
except KeyboardInterrupt:
    pass
finally:
    try:
        ble.active(0)
    except Exception:
        pass
    print("BLE stop")

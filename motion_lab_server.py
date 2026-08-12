# -*- coding: utf-8 -*-
"""STeaMi Motion Lab - serveur BLE GATT (5 capteurs) + OLED rond.
Nom BT: ExAOlib. Service: 8B9D0001-8D4C-4F3A-9B1A-2C3D4E5F6A7B.
Autodemarrage si copie vers main.py.

Trame NOTIFY (CSV, 5 Hz, 15 champs):
  ax,ay,az,gx,gy,gz,mx,my,mz,dist,press,temp,hum,temp2,lum
  ax..az : acceleration (g)      gx..gz : rotation (deg/s)
  mx..mz : magneto              dist   : distance ToF (mm)
  press/temp : WSEN-PADS        hum/temp2 : WSEN-HIDS
  lum : luminosite (APDS-9960)

FIX STABILITE (2026-08): le travail lourd (lecture 5 capteurs I2C +
dessin OLED) est fait a 5 Hz avec un sleep_ms(200) dans CHAQUE branche
(de la boucle, connecte comme non-connecte). Sans ce sleep, la boucle
monopolise le microcontroleur et le stack BLE ne traite plus les IRQ
(connexion/decouverte GATT/deconnexion) -> le central se fait deconnecter
quasi immediatement (symptome "se deconnecte apres 0,1 s"). Avec le sleep,
la decouverte GATT reussit et la connexion tient.
"""
import time
from micropython import const
from machine import I2C, SPI, Pin
import bluetooth
from bluetooth import BLE, UUID
from ism330dl import ISM330DL
from lis2mdl import LIS2MDL
from vl53l1x import VL53L1X
from wsen_pads import WSEN_PADS
from wsen_hids import WSEN_HIDS
from apds_native.apds_native import APDSNative
import ssd1327

_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)

_SENSOR_UUID = UUID("8b9d0001-8d4c-4f3a-9b1a-2c3d4e5f6a7b")
_DATA_UUID = UUID("8b9d0002-8d4c-4f3a-9b1a-2c3d4e5f6a7b")

spi = SPI(1)
raw = ssd1327.WS_OLED_128X128_SPI(spi, Pin("DATA_COMMAND_DISPLAY"),
                                  Pin("RST_DISPLAY"), Pin("CS_DISPLAY"))
fb = raw.framebuf

i2c = I2C(1)
imu = ISM330DL(i2c)
mag = LIS2MDL(i2c)
dist = VL53L1X(i2c)
dist.start_ranging()
press = WSEN_PADS(i2c)
hum = WSEN_HIDS(i2c)
lum = APDSNative(i2c)

ble = BLE()
ble.active(1)
_connh = None
_notif = 0


def _irq(event, data):
    global _connh
    if event == _IRQ_CENTRAL_CONNECT:
        _connh, _, _ = data
    elif event == _IRQ_CENTRAL_DISCONNECT:
        _connh = None
        ble.gap_advertise(20000, adv)


def read_all():
    ax, ay, az = imu.acceleration_g()
    gx, gy, gz = imu.gyroscope_dps()
    try:
        mx, my, mz = mag.read_one_shot()
    except Exception:
        mx = my = mz = 0
    try:
        d = dist.read()
    except Exception:
        d = -1
    try:
        p = press.pressure_hpa(); pt = press.temperature()
    except Exception:
        p = pt = -1
    try:
        ht, tt = hum.read_one_shot()
    except Exception:
        ht = tt = -1
    try:
        l = lum.luminance()
    except Exception:
        l = -1
    return ax, ay, az, gx, gy, gz, mx, my, mz, d, p, pt, ht, tt, l


def draw(connected, vals):
    ax, ay, az, gx, gy, gz, mx, my, mz, d, p, pt, ht, tt, l = vals
    fb.fill(0)
    lines = [
        "ExAOlib",
        ("BT:CONNECTE" if connected else "BT:ACTIF"),
        "A %.2f %.2f %.2f" % (ax, ay, az),
        "G %.1f %.1f %.1f" % (gx, gy, gz),
        "M %d %d %d" % (mx, my, mz),
        "D %dmm P %.0fh" % (d, p),
        "T %.1fC H %.0f%%" % (tt, ht),
        "L %d" % l,
        "N %d" % _notif,
    ]
    yy = 18
    for i, ln in enumerate(lines):
        x = 64 - len(ln) * 4
        col = 15 if i == 0 else 9
        fb.text(ln, x, yy, col)
        yy += 13
    raw.show()


srv = (_SENSOR_UUID, ((_DATA_UUID, bluetooth.FLAG_READ | bluetooth.FLAG_NOTIFY),))
(adv_srv,) = ble.gatts_register_services((srv,))
_data_handle = adv_srv[0]

_UUID_STR = "8b9d0001-8d4c-4f3a-9b1a-2c3d4e5f6a7b"
_le = bytes(reversed(bytes.fromhex(_UUID_STR.replace("-", ""))))
_name = b"ExAOlib"
adv = (b"\x02\x01\x06" + b"\x11\x07" + _le
       + bytes([len(_name) + 1, 0x09]) + _name)

ble.irq(_irq)
print("ExAOlib BLE serveur (5 capteurs) + OLED [LIGHT]")
ble.gap_advertise(20000, adv)

n = 0
last = (0,0,0,0,0,0,0,0,0,-1,-1,-1,-1,-1,-1)
try:
    while True:
        if _connh is not None:
            # travail lourd UNIQUEMENT si connecte
            v = read_all()
            s = "%.3f,%.3f,%.3f,%.2f,%.2f,%.2f,%d,%d,%d,%d,%.1f,%.1f,%.1f,%.1f,%d" % v
            ble.gatts_write(_data_handle, s.encode())
            try:
                ble.gatts_notify(_connh, _data_handle, s.encode())
                _notif += 1
            except Exception:
                pass
            draw(True, v)
            last = v
            n += 1
            if n % 10 == 0:
                print("sample:", s)
            time.sleep_ms(200)  # laisse le stack BLE traiter les IRQs (decouverte/déconnexion)
        else:
            draw(False, last)
            time.sleep_ms(200)
except KeyboardInterrupt:
    pass
finally:
    try:
        ble.active(0)
    except Exception:
        pass
    print("BLE stop")

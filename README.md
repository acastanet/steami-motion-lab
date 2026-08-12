# STeaMi Motion Lab (MVP)

Laboratoire scientifique sans fil : une carte STeaMi (capteurs VL53L1X + IMU ISM330DLC)
diffuse ses mesures par BLE vers une web app Android.

## Contenu
- `motion_lab_server.py` : serveur BLE GATT pour la STeaMi (deployer vers `main.py`).
- `motion_lab_app.html` : application Android (Web Bluetooth)
  -> https://acastanet.github.io/steami-motion-lab/motion_lab_app.html
- `motion_lab_tutoriel.html` : tutoriel pedagogique.

## Deploy carte
    mpremote connect COM3 cp motion_lab_server.py :main.py

## Android
Ouvrir l'URL ci-dessus dans Chrome, bouton Connecter, choisir STeaMi-Motion.
Le Web Bluetooth exige HTTPS (fourni par GitHub Pages) ou localhost.

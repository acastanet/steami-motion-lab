# STeaMi Reference — faits stables

Fiche référence (matériel + protocole) pour le projet STeaMi Motion Lab. Stable : ne pas modifier sauf changement de hardware/firmware. Le *comment opérer* est dans `AGENT_WORKFLOW.md`.

## 1. Matériel

- **Carte** : STeaMi, fork MicroPython **v0.23.1**. REPL baud = 9600.
- **Drivers** (dans `drivers_lib/` côté code de travail) : `ism330dl` (IMU 6 axes), `vl53l1x` (ToF), `lis2mdl` (magnéto), `wsen_pads` (pression+temp), `wsen_hids` (temp+hum), `apds_native` (lumière), `ssd1327` (OLED rond 128×128).
- **Broches / connecteurs** :
  - **J3 / J4 = Qwiic = I²C3 = PC0 / PC1** (PAS UART — erreur fréquente).
  - **LPUART1 = PB10 / PB11** (« LP1 ») n'est **pas** sur le edge connector.
  - **J5 / J6 Jacdac** : tied 0R, half-duplex 5 V.
- **LEDs** :
  - 4 LEDs interface (F103) : charge (RED), COM (GRN R61=47R), DAP (BLUE R58=120R), STLINK → **non drivables depuis MicroPython**.
  - 4 LEDs user WB55 : RGB = PC10/11/12, BLE = PH3 → **drivables mais PAS de PWM matériel** (ValueError) → on/off ou software-PWM uniquement.
- **Alim** : l'edge 3V3 **sag** sous charge → alimenter les modules depuis le 3V3 SWD si besoin.

## 2. Protocole Motion Lab (serveur ExAOlib)

- **Nom BT** : `ExAOlib`.
- **Service** : `8B9D0001-8D4C-4F3A-9B1A-2C3D4E5F6A7B`.
- **Caractéristique DATA** : `8B9D0002-8D4C-4F3A-9B1A-2C3D4E5F6A7B` (READ + NOTIFY).
- **Trame NOTIFY** : CSV, **5 Hz**, **15 champs** :
  ```
  ax,ay,az,gx,gy,gz,mx,my,mz,dist,press,temp,hum,temp2,lum
  ```
  - `ax..az` : accélération (g)
  - `gx..gz` : rotation (°/s)
  - `mx..mz` : magnétomètre
  - `dist` : distance ToF (mm) — **index 9** (champ 10)
  - `press, temp` : WSEN-PADS
  - `hum, temp2` : WSEN-HIDS
  - `lum` : luminosité (APDS-9960)
- **MVP** (interface web) = seulement **distance + accélération + rotation** :
  - distance = champ `dist` (idx 9)
  - `|a| (g) = hypot(ax, ay, az)`
  - `|ω| (°/s) = hypot(gx, gy, gz)`
  - Les autres capteurs sont transmis mais **volontairement ignorés** par l'app MVP.
- Pas de caractéristique CMD/STATUS dans le serveur d'origine : l'acquisition tourne en continu à 5 Hz dès la connexion.

## 3. Web App (Android)

- **URL** : `https://acastanet.github.io/steami-motion-lab/motion_lab_app.html` (Chrome Android, HTTPS obligatoire).
- Vise le service `8b9d0001-…`, la DATA `8b9d0002-…`.
- Parser : attend **≥ 15 champs**, extrait `dist` (idx 9), `ax/ay/az` (0-2), `gx/gy/gz` (3-5). Chrono calculé côté app (1re notification = t0).
- Boutons : Connecter / Reset / Demo / Exporter CSV. Mode Démo = courbes synthétiques sans carte.
- Export CSV : `t_ms, distance_mm, ax, ay, az, gx, gy, gz`.

## 4. Arborescence repo

- **`steami-motion-lab`** (ce repo) : livrables versionnés — `motion_lab_app.html`, `motion_lab_tutoriel.html`, `motion_lab_server.py`, `AGENT_WORKFLOW.md`, `STeaMi_REFERENCE.md`. Branches `main` (source) + `gh-pages` (site en ligne).
- **`C:\DEV_ALX\Steami`** (code de travail, hors repo) : `ble_sensors.py` (serveur 5 capteurs d'origine), `drivers_lib/`, `ble_sensors_light.py` (serveur corrigé, base de `motion_lab_server.py`), `main.py.bak` (backup de l'ancien `main.py`), outils de diag (`ble_diag*.py`, `ble_minimal_test.py`).

# Guide pratique — documentation STeaMi et capteurs

Où trouver la documentation de la carte STeaMi, des principaux capteurs, et des bibliothèques MicroPython utilisées dans ce projet. Document de référence pour aller plus loin.

> Ce guide fait partie du bilan d'un atelier **IA et Microcontrôleur** : il rassemble les sources utiles pour reproduire ou étendre le projet STeaMi Motion Lab.

## 1. La carte STeaMi

La STeaMi est une carte pédagogique programmable en MicroPython, basée sur un microcontrôleur STM32WB55 (Bluetooth Low Energy) et équipée de plusieurs capteurs MEMS + un écran OLED.

- **MicroPython (général)** : https://micropython.org/ — documentation langage et API : https://docs.micropython.org/
- **Bluetooth Low Energy sous MicroPython** : https://docs.micropython.org/en/latest/library/ubluetooth.html
- **`mpremote` (outil de flash / REPL)** : https://docs.micropython.org/en/latest/reference/mpremote.html
- **Dépôt MicroPython (pour forker / builder un firmware)** : https://github.com/micropython/micropython

> Note : la STeaMi utilise un fork MicroPython (v0.23.1 dans ce projet). Se référer au dépôt fourni avec la carte pour le firmware exact et les drivers préinstallés.

## 2. Principaux capteurs et leur documentation constructeur

Tous les capteurs sont des produits **STMicroelectronics**. La documentation de référence (datasheet, application notes) se trouve sur le site produit `st.com` (page « Documentation » / « Datasheet »).

| Capteur | Rôle | Page produit ST | Datasheet |
|---------|------|-----------------|-----------|
| **VL53L1X** | Distance Time-of-Flight (ToF), jusqu'à 4 m | https://www.st.com/en/imaging-and-photonics-solutions/vl53l1x.html | https://www.st.com/resource/en/datasheet/vl53l1x.pdf |
| **ISM330DLC** | IMU 6 axes (accéléromètre 3 axes + gyroscope 3 axes) | https://www.st.com/en/mems-and-sensors/ism330dlc.html | https://www.st.com/resource/en/datasheet/ism330dlc.pdf |
| **LIS2MDL** | Magnétomètre 3 axes | https://www.st.com/en/mems-and-sensors/lis2mdl.html | https://www.st.com/resource/en/datasheet/lis2mdl.pdf |
| **WSEN-PADS** | Pression atmosphérique + température | https://www.st.com/en/mems-and-sensors/wsen-pads.html | (voir page produit, section Documentation) |
| **WSEN-HIDS** | Humidité + température | https://www.st.com/en/mems-and-sensors/wsen-hids.html | (voir page produit, section Documentation) |
| **APDS-9960** | Lumière / proximité / couleur (module utilisé ici en mode luminosité) | https://www.st.com/en/ ... (réf. constructeur modules) | datasheet constructeur du module |

Conseil : pour chaque capteur, ouvrir la **page produit ST** puis l'onglet **Documentation** donne le datasheet à jour, les application notes et parfois le code d'exemple C (API).

## 3. Où se trouvent les bibliothèques (drivers)

Dans ce projet, les drivers MicroPython des capteurs ne sont **pas** sur PyPI : ils sont livrés avec le firmware / le dépôt de la carte, dans un dossier `drivers_lib/`.

- **Emplacement (code de travail)** : `C:\DEV_ALX\Steami\drivers_lib\` — contient notamment :
  - `ism330dl.py` (IMU)
  - `vl53l1x.py` (ToF)
  - `lis2mdl.py` (magnéto)
  - `wsen_pads.py` (pression+temp)
  - `wsen_hids.py` (humidité+temp)
  - `apds_native/` (luminosité, module natif)
  - `ssd1327.py` (écran OLED rond)
- **Serveur de référence** : `C:\DEV_ALX\Steami\ble_sensors.py` (serveur 5 capteurs d'origine) et `ble_sensors_light.py` (version corrigée, base de `motion_lab_server.py` dans ce repo).
- **Dans ce repo (`steami-motion-lab`)** : `motion_lab_server.py` est le serveur BLE versionné et prêt à flasher.

> Si les drivers ne sont pas présents sur la carte, le serveur démarre quand même (init résiliente) mais les capteurs manquants renvoient des valeurs par défaut. Pour ajouter un capteur, copier le driver correspondant dans `drivers_lib/` et l'importer dans le serveur.

## 4. Références pédagogiques (contexte du MVP)

Le MVP s'appuie sur des références institutionnelles et scientifiques (détaillées dans `motion_lab_tutoriel.html`) :
- Éduscol — informatique industrielle au cycle 4 : https://eduscol.education.gouv.fr/7022/l-informatique-industrielle-au-coeur-de-la-technologie-au-cycle-4
- Bouquet et al., *Enhance your smartphone with a Bluetooth Arduino nano board*, Physics Education 57(1), 2022 : https://doi.org/10.1088/1361-6552/ac35af
- phyphox (BLE + smartphone scientifique) : https://phyphox.org/ble/

## 5. Pour aller plus loin

- Ajouter un capteur au serveur : voir `STeaMi_REFERENCE.md` (broches, protocole).
- Comprendre le déploiement / les pièges BLE : voir `AGENT_WORKFLOW.md`.
- Reproduire l'expérience côté smartphone : voir `motion_lab_tutoriel.html` et l'app `motion_lab_app.html`.

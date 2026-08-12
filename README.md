# STeaMi Motion Lab (MVP)

Laboratoire scientifique sans fil : une carte STeaMi (capteurs VL53L1X + IMU ISM330DLC)
diffuse ses mesures par BLE vers une web app Android.

> **Bilan d'un atelier IA et Microcontrôleur** : ce dépôt rassemble le matériel
> produit lors d'un atelier croisant intelligence artificielle et microcontrôleurs,
> autour d'une carte STeaMi instrumentée et d'un smartphone.

## Contenu du dépôt

- `motion_lab_server.py` : serveur BLE GATT pour la STeaMi (à déployer vers `main.py`).
- `motion_lab_app.html` : application Android (Web Bluetooth)
  → https://acastanet.github.io/steami-motion-lab/motion_lab_app.html
- `motion_lab_tutoriel.html` : tutoriel pédagogique du MVP.
- `GUIDE_PRATIQUE.md` : où trouver la documentation STeaMi, des capteurs et des bibliothèques.
- `AGENT_WORKFLOW.md` : comment déployer et tester sans casser le serveur (flash, pièges BLE).
- `STeaMi_REFERENCE.md` : référence matérielle et protocole (broches, trame BLE).

## Déploiement carte

    mpremote connect COM3 cp motion_lab_server.py :main.py

La carte diffuse sous le nom **ExAOlib** (service `8B9D0001-…`), à 5 Hz.

## Android

Ouvrir l'URL ci-dessus dans Chrome, bouton Connecter, choisir **ExAOlib**.
Le Web Bluetooth exige HTTPS (fourni par GitHub Pages) ou localhost.

## Documentation en ligne

- Application : https://acastanet.github.io/steami-motion-lab/motion_lab_app.html
- Tutoriel : https://acastanet.github.io/steami-motion-lab/motion_lab_tutoriel.html
- Guide pratique (doc STeaMi + capteurs + libs) : https://acastanet.github.io/steami-motion-lab/GUIDE_PRATIQUE.md
- Guide agent (workflow + référence) : https://acastanet.github.io/steami-motion-lab/AGENT_WORKFLOW.md et https://acastanet.github.io/steami-motion-lab/STeaMi_REFERENCE.md

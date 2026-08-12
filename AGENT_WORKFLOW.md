# Agent Workflow — STeaMi Motion Lab

Comment un agent (assistant IA de coding) doit travailler avec la carte STeaMi sans casser le déploiement. Document opérationnel, à lire avant toute manipulation de la carte ou du repo.

## 1. Vue d'ensemble

Ce document décrit le *comment* : outils, flash, tests, et pièges rencontrés en vrai.
La fiche matériel/protocole stable est dans `STeaMi_REFERENCE.md`.
Le MVP pédagogique et son protocole sont dans `motion_lab_tutoriel.html`.

Règle d'or de l'utilisateur : **tester, pas supposer**. Isoler la cause par l'expérience plutôt que de conjecturer. Max une passe de vérification après un changement.

## 2. Environnement

- **OS** : Windows (Hermes desktop app). Le shell est bash (git-bash/MSYS), pas PowerShell.
- **STeaMi** : fork MicroPython v0.23.1. Baud REPL = 9600 (remettre 9600 après un flash en 115200).
- **Outils PC** :
  - `mpremote` (flash, ls, cp, reset, run). Défauts dans `.mpremote` (`baudrate 9600`, `port auto`).
  - Python 3.11 + `bleak` pour écrire un **central BLE de test** (se connecter, lire la trame, vérifier la stabilité).
  - `node` pour vérifier la syntaxe JS des pages web (`vm.compileFunction`).
- **Repo** : `steami-motion-lab` (web + serveur versionnés) vs `C:\DEV_ALX\Steami` (code de travail, drivers, `main.py.bak`).

## 3. Flash & déploiement fiable

Le transport raw-paste de `mpremote` est **flaky** : un `cp` peut dire « OK » alors que le fichier est corrompu sur la carte (taille identique mais contenu partiel → crash au boot).

Procédure sûre :

```bat
rem 1) flash en 115200 (plus fiable pour les gros fichiers)
printf 'baudrate 115200\nport COM7\n' > .mpremote
mpremote connect COM7 rm :main.py
mpremote connect COM7 cp ton_fichier.py :main.py
rem 2) remettre 9600
printf 'baudrate 9600\nport auto\n' > .mpremote
rem 3) VERIFIER par lecture-retour (diff CRC)
mpremote connect COM7 cp :main.py /tmp/board_main.py
diff ton_fichier.py /tmp/board_main.py && echo FLASH OK || echo CORROMPU
```

- En cas d'échec, **boucle de retries** (3-5 essais) : `rm` puis `cp`.
- `COM7` est le port observé ici ; vérifier avec `mpremote` nu (affiche `Connected to MicroPython at COMx`) ou `pyserial` `comports()`.
- Après flash vers `main.py`, faire un **reset** (`mpremote reset`) pour relancer le serveur depuis le boot.

## 4. REPL — ne jamais tuer main.py par accident

- `mpremote run fichier.py` **ouvre le REPL et exécute le script en RAM** → cela **stoppe le `main.py` en cours d'exécution**. Ne pas le faire si on veut garder le serveur vivant.
- Pour diagnostiquer la carte **sans tuer le serveur** : lire un fichier (`mpremote cp :fichier .`) plutôt qu'ouvrir le REPL.
- Si `mpremote` reste bloqué (`could not enter raw repl`, `no device found`, `PermissionError: ClearCommError failed`) : le port COM est verrouillé par une session REPL ouverte. **Débrancher/rebrancher la carte** (reset matériel USB) puis réessayer.

## 5. BLE sous MicroPython — le piège majeur

Symptôme typique : la carte **s'annonce** (scan OK) mais le central se **déconnecte quasi immédiatement** dès la connexion / découverte GATT (« se déconnecte après 0,1 s »).

Cause racine : la boucle principale fait du travail lourd à chaque itération — `read_all()` (5 capteurs I2C) + `draw()` (OLED SPI) — **sans pause**. Le microcontrôleur est monopolisé, le stack BLE ne traite plus les IRQ (connexion, découverte GATT, déconnexion). `_connh` reste coincé sur une vieille valeur, la découverte GATT échoue, déconnexion immédiate.

Fix (validé) :

```python
while True:
    if _connh is not None:
        v = read_all()          # travail lourd
        # ... gatts_notify ...
        draw(True, v)
        time.sleep_ms(200)       # pause OBLIGATOIRE (branche connectée)
    else:
        draw(False, last)
        time.sleep_ms(200)       # pause (branche non connectee)
```

Le `sleep_ms(200)` (~5 Hz) laisse le stack BLE respirer. **Sans ce sleep dans les DEUX branches, la connexion ne tient pas.**
Contrôle : un serveur BLE **minimal** (1 service, 1 char, pas de I2C/OLED, avec sleep) passe la découverte GATT (`SERVICE TROUVE`) — preuve que le firmware WB55 gère le GATT, le bug est dans la boucle lourde.

## 6. Tests empiriques (isoler carte vs central)

Pour savoir si un bug est côté carte ou côté client (Chrome/Android) :

1. **Central PC (bleak)** se connecte-t-il et tient-il ? Si le PC se fait aussi déconnecter → bug carte. Si le PC tient et Android non → spécifique Android (MTU, paramètres).
2. **Test nu** : connecter sans faire de `get_service` (découverte GATT) → la connexion tient-elle ? Si oui → c'est la découverte GATT qui plante (cf. section 5).
3. **Serveur minimal** de référence pour isoler firmware vs serveur (cf. section 5).

Scanner depuis le PC est **instable** (scans qui ratent aléatoirement) → ne pas conclure d'un seul scan vide ; refaire 2-3 fois. La vraie cible de test reste Android (Chrome).

## 7. Pièges & solutions

| Piège | Symptôme | Solution |
|-------|----------|----------|
| Flash corrompu | `main.py` ne démarre pas, carte muette | Boucle retries + **vérif lecture-retour (diff)** |
| REPL ouvert tue le serveur | Connexion perdue après un `mpremote run` | Ne pas ouvrir le REPL si le serveur doit tourner ; `cp` fichier pour diagnostiquer |
| Port bloqué | `no device found` / `PermissionError` | Débrancher/rebrancher la carte (reset USB) |
| Boucle lourde sans sleep | Déconnexion immédiate au connect | `time.sleep_ms(200)` dans les deux branches |
| `cp` « same file » | On croit avoir copié mais le fichier est identique à la destination | Copier depuis la bonne source (ex. `git checkout main -- fichier`) |
| Sync `gh-pages` ratée | L'URL sert l'ancienne version | `git checkout main -- fichier` puis commit/push sur `gh-pages` ; attendre le build GitHub Pages (~30 s) |
| Scan PC vide | `ANNONCES: RIEN` | Refaire le scan ; l'adaptateur BT PC est capricieux |

## 8. Déploiement web (rappel)

- Web Bluetooth exige **HTTPS** (ou localhost). `file://` ne marche pas.
- Pages servies via **GitHub Pages** (`gh-pages`) : `https://acastanet.github.io/steami-motion-lab/...`.
- Après push sur `gh-pages`, **attendre le rebuild** (~30 s) avant de révérif l'URL.

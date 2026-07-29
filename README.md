# camtraps-frames

Extrait des frames depuis des vidéos de pièges photographiques, avec des
métadonnées EXIF (date de prise de vue) lues depuis les métadonnées internes
de la vidéo — pas depuis le système de fichiers, qui ment dès qu'un fichier a
été copié ou déplacé.

## Prérequis

- Python ≥ 3.9
- [ffmpeg](https://ffmpeg.org/download.html) installé et accessible dans le PATH (fournit `ffprobe`)
  ```bash
  conda install -c conda-forge ffmpeg   # ou
  brew install ffmpeg                   # macOS
  sudo apt install ffmpeg               # Linux
  ```

## Installation

Depuis le dossier du projet :
```bash
pip install .
```

Pour développer/modifier le package (les changements sont pris en compte sans réinstaller) :
```bash
pip install -e .
```

Utilisation dans Jupyter (progress bars enrichies) :
```bash
pip install ".[notebook]"
```

## Utilisation

### 1. En ligne de commande

```bash
camtraps-frames /chemin/vers/dossier --interval 2 --delay 0.1 --recursive
camtraps-frames /chemin/vers/video.mp4 --resize 0.5
camtraps-frames --help
```

### 2. Dans un script Python

```python
from camtraps_frames import extract_frames

extract_frames(
    "/chemin/vers/dossier",
    interval_s=2,
    delay_s=0.1,
    resize_factor=1,
    recursive=True,
    tz="Europe/Brussels",
)
```

### 3. Dans Jupyter (comme avant)

```python
from camtraps_frames import extract_frames
extract_frames("/chemin/vers/dossier", interval_s=2, recursive=True)
```

### 4. Fonctions bas niveau

Pour des besoins plus spécifiques (traiter une seule vidéo, lire uniquement
la date de création, etc.) :

```python
from camtraps_frames import get_creation_time, extract_frames_from_video_file

date = get_creation_time("video.mp4", tz="Europe/Brussels")

extract_frames_from_video_file(
    "video.mp4", "dossier_sortie",
    interval_s=1, delay_s=0.5, resize=None,
)
```

## Paramètres principaux

| Paramètre        | Description                                                        | Défaut             |
|-------------------|----------------------------------------------------------------------|---------------------|
| `interval_s`      | Intervalle en secondes entre deux frames extraites                  | `1`                 |
| `delay_s`         | Délai en secondes avant la première frame                           | `0.5`               |
| `resize_factor`   | Facteur de redimensionnement (0 < x ≤ 1), `None` = taille originale | `None`              |
| `recursive`       | Parcourt aussi les sous-dossiers                                     | `False`             |
| `tz`              | Fuseau horaire IANA du piège photo                                    | `"Europe/Brussels"` |
| `exif_template_path` | Chemin vers un `.JPG` pour un template EXIF personnalisé (GPS, etc.) | `None` (auto)      |
| `sound`           | Joue un son de fin (macOS/Windows/bip terminal)                     | `True`              |
| `verbose`         | `0` silencieux · `1` résumé compact (défaut en Python) · `2` détaillé (défaut en CLI) | `1` / `2` |

### Verbosité et Jupyter

Avec `verbose=1` (défaut en usage Python/notebook), la sortie reste sur une seule
ligne de statut : en notebook, elle est automatiquement effacée et remplacée à
chaque dossier traité (`clear_output` détecté et géré automatiquement — inutile
d'y penser). Les avertissements (vidéos sans métadonnées exploitables, etc.) sont
regroupés dans un résumé compact affiché à la toute fin, plutôt qu'imprimés un
par un pendant le traitement.

- `verbose=0` : rien, sauf en cas d'erreur bloquante.
- `verbose=1` : une ligne de statut + résumé final (dossiers traités, avertissements).
- `verbose=2` : comportement complet (liste des dossiers trouvés, barres de
  progression par vidéo, avertissements affichés au fil de l'eau).

La CLI utilise `verbose=2` par défaut (un terminal ne pose pas le même problème
d'accumulation qu'un notebook) ; utilise `--verbose 1` ou `--verbose 0` pour réduire.

## Comportement

- Une vidéo sans métadonnées `creation_time` exploitables est **signalée et ignorée**,
  le reste du batch continue normalement.
- Avec `recursive=True`, un seul dossier `output_<nom>` est créé à côté du dossier
  racine, avec la même arborescence que la source.
- Sans `recursive`, chaque vidéo/dossier traité produit son propre `output_<nom>`
  à côté de la source.

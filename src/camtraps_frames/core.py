"""
Extraction de frames depuis des vidéos de pièges photographiques,
avec réécriture des métadonnées EXIF (date de prise de vue réelle).

Ce module ne dépend d'aucun environnement particulier : il fonctionne
aussi bien dans un script Python classique, dans Jupyter, ou via la CLI
fournie par ce package (voir cli.py).
"""

import os
import sys
import json
import shutil
import platform
import subprocess
import datetime
from zoneinfo import ZoneInfo

import cv2
import piexif
from PIL import Image
from tqdm.auto import tqdm

VIDEO_EXTENSIONS = (".mov", ".mp4", ".avi")

# Si exif_template_path vaut None (défaut), un template minimal est généré en
# mémoire (aucun fichier externe requis). Passer un chemin vers un .JPG existant
# pour utiliser un template personnalisé (ex: avec GPS, modèle d'appareil, etc.)
DEFAULT_EXIF_TEMPLATE = None


def _default_exif_dict():
    return {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}


def _in_notebook():
    """Détecte si le code s'exécute dans un notebook Jupyter (pas dans un
    terminal IPython classique)."""
    try:
        from IPython import get_ipython
        shell = get_ipython()
        return shell is not None and "ZMQInteractiveShell" in type(shell).__name__
    except Exception:
        return False


def _clear(verbose):
    """En notebook, efface la sortie précédente pour ne garder qu'une ligne de
    statut à l'écran. Ne fait rien en terminal (où ça n'aurait pas de sens)."""
    if verbose <= 1 and _in_notebook():
        from IPython.display import clear_output
        clear_output(wait=True)


class _Warnings:
    """Accumule les avertissements au lieu de les imprimer un par un ;
    affichés en un résumé compact à la fin (sauf en verbose=2, où ils
    s'affichent aussi au fil de l'eau, comportement le plus verbeux)."""

    def __init__(self, verbose=1):
        self.verbose = verbose
        self.items = []

    def add(self, msg):
        self.items.append(msg)
        if self.verbose >= 2:
            print(f"⚠️ {msg}")

    def print_summary(self):
        if not self.items:
            return
        if self.verbose == 0:
            return
        print(f"\n⚠️ {len(self.items)} avertissement(s) :")
        for msg in self.items:
            print(f"  - {msg}")


def _ensure_ffprobe():
    if shutil.which("ffprobe") is None:
        raise EnvironmentError(
            "ffprobe introuvable. Installe ffmpeg :\n"
            "  conda install -c conda-forge ffmpeg\n"
            "  ou : brew install ffmpeg (macOS) / apt install ffmpeg (Linux) / "
            "voir https://ffmpeg.org/download.html (Windows)"
        )


def get_creation_time(path, tz="Europe/Brussels", warnings=None):
    """Extrait la date de création depuis les métadonnées internes de la vidéo
    (creation_time du conteneur mp4/mov), convertie de UTC vers le fuseau `tz`.

    Retourne None si aucune métadonnée exploitable n'est trouvée. Le message
    correspondant est ajouté à `warnings` (accumulateur _Warnings) si fourni,
    sinon imprimé directement (utile en usage bas niveau, hors batch).
    """
    _ensure_ffprobe()

    def _warn(msg):
        if warnings is not None:
            warnings.add(msg)
        else:
            print(f"⚠️ {msg}")

    cmd = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        info = json.loads(result.stdout)
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        _warn(f"Impossible de lire les métadonnées de {os.path.basename(path)} : {e}")
        return None

    creation_str = info.get("format", {}).get("tags", {}).get("creation_time")

    if creation_str is None:
        _warn(f"Pas de creation_time exploitable dans les métadonnées de {os.path.basename(path)}")
        return None

    try:
        dt_utc = datetime.datetime.strptime(
            creation_str, "%Y-%m-%dT%H:%M:%S.%fZ"
        ).replace(tzinfo=ZoneInfo("UTC"))
    except ValueError as e:
        _warn(f"Format de creation_time inattendu dans {os.path.basename(path)} ({creation_str!r}) : {e}")
        return None

    return dt_utc.astimezone(ZoneInfo(tz)).replace(tzinfo=None)


def _resize_image(image, resize_factor):
    new_width = int(image.width * resize_factor)
    new_height = int(image.height * resize_factor)
    return image.resize((new_width, new_height))


def _get_output_folder(source_path):
    """output_<nom> créé à côté du fichier ou dossier source."""
    if os.path.isfile(source_path):
        base_dir = os.path.dirname(source_path)
        name = os.path.splitext(os.path.basename(source_path))[0]
    else:
        base_dir = os.path.dirname(source_path)
        name = os.path.basename(os.path.normpath(source_path))

    output_folder = os.path.join(base_dir, f"output_{name}")
    os.makedirs(output_folder, exist_ok=True)
    return output_folder


def _notify(sound=True):
    """Bip de fin, silencieux et sans erreur si non disponible (multiplateforme)."""
    if not sound:
        return
    try:
        system = platform.system()
        if system == "Darwin":
            subprocess.run(
                ["afplay", "/System/Library/Sounds/Submarine.aiff"],
                check=False, timeout=5,
            )
        elif system == "Windows":
            import winsound
            winsound.MessageBeep()
        else:
            sys.stdout.write("\a")
            sys.stdout.flush()
    except Exception:
        pass  # le son est un confort, jamais bloquant


def extract_frames_from_video_file(
    path,
    output_folder,
    interval_s=1,
    delay_s=0.5,
    resize=None,
    tz="Europe/Brussels",
    exif_template_path=DEFAULT_EXIF_TEMPLATE,
    verbose=1,
    warnings=None,
):
    """Extrait les frames d'une seule vidéo vers output_folder."""

    def _warn(msg):
        if warnings is not None:
            warnings.add(msg)
        else:
            print(f"⚠️ {msg}")

    exif_template = piexif.load(exif_template_path) if exif_template_path else _default_exif_dict()
    video = cv2.VideoCapture(path)

    fps = video.get(cv2.CAP_PROP_FPS)
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

    if fps == 0 or total_frames == 0:
        _warn(f"Fichier ignoré (illisible) : {os.path.basename(path)}")
        video.release()
        return

    creation_time = get_creation_time(path, tz=tz, warnings=warnings)
    if creation_time is None:
        _warn(f"Vidéo ignorée (pas de métadonnées exploitables) : {os.path.basename(path)}")
        video.release()
        return

    frames_gap = int(fps * interval_s)
    delay = int(delay_s * fps)
    index_to_extract = list(range(delay, total_frames, frames_gap))
    file_name = os.path.splitext(os.path.basename(path))[0]

    frame_iter = index_to_extract
    if verbose >= 2:
        frame_iter = tqdm(index_to_extract, desc=os.path.basename(path), leave=False, unit="img")

    for i, frame_index in enumerate(frame_iter):
        video.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = video.read()
        if not ret:
            continue

        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        if resize:
            image = _resize_image(image, resize)

        timestamp = creation_time + datetime.timedelta(seconds=frame_index / fps)

        exif_template["Exif"][piexif.ExifIFD.DateTimeOriginal] = timestamp.strftime("%Y:%m:%d %H:%M:%S")
        exif_template["Exif"][piexif.ExifIFD.DateTimeDigitized] = timestamp.strftime("%Y:%m:%d %H:%M:%S")
        exif_bytes = piexif.dump(exif_template)

        output_path = os.path.join(output_folder, f"{file_name}_{i}.jpg")
        image.save(output_path, "JPEG", exif=exif_bytes)

    video.release()


def extract_frames_from_video_folder(folder, output_folder=None, verbose=1, warnings=None, **kwargs):
    """Traite toutes les vidéos d'un dossier (non récursif)."""

    if output_folder is None:
        output_folder = _get_output_folder(folder)
    else:
        os.makedirs(output_folder, exist_ok=True)

    videos = [
        os.path.join(folder, f)
        for f in sorted(os.listdir(folder))
        if f.lower().endswith(VIDEO_EXTENSIONS)
    ]

    if not videos:
        msg = f"Aucune vidéo trouvée directement dans : {folder}"
        if warnings is not None:
            warnings.add(msg)
        elif verbose >= 1:
            print(f"⚠️ {msg}")
        return

    video_iter = videos
    if verbose >= 1:
        video_iter = tqdm(
            videos, desc=os.path.basename(folder) or folder, leave=(verbose >= 2), unit="video"
        )

    for path in video_iter:
        extract_frames_from_video_file(path, output_folder, verbose=verbose, warnings=warnings, **kwargs)

    if verbose >= 2:
        print(f"✓ Dossier terminé : {folder} ({len(videos)} vidéos)")


def _find_video_folders(root):
    """Dossiers contenant au moins une vidéo, en ignorant output_* déjà générés."""
    video_folders = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith("output_")]
        if any(f.lower().endswith(VIDEO_EXTENSIONS) for f in filenames):
            video_folders.append(dirpath)
    return video_folders


def extract_frames_recursive(root_folder, sound=True, verbose=1, **kwargs):
    """Parcourt récursivement root_folder et recrée son arborescence dans un
    unique dossier de sortie output_<nom> à côté de root_folder."""

    video_folders = _find_video_folders(root_folder)
    warnings = _Warnings(verbose=verbose)

    if not video_folders:
        print(f"⚠️ Aucun dossier contenant des vidéos n'a été trouvé sous : {root_folder}")
        return

    root_output = _get_output_folder(root_folder)

    if verbose >= 2:
        print(f"{len(video_folders)} dossier(s) contenant des vidéos trouvé(s) :")
        for f in video_folders:
            print(f"  - {f}")
        print(f"\nDossier de sortie global : {root_output}\n")

    folder_iter = video_folders
    if verbose >= 1:
        folder_iter = tqdm(video_folders, desc="Dossiers", unit="dossier", leave=(verbose >= 2))

    for folder_i, folder in enumerate(folder_iter, start=1):
        rel_path = os.path.relpath(folder, root_folder)
        sub_output = root_output if rel_path == "." else os.path.join(root_output, rel_path)

        if verbose == 1:
            _clear(verbose)
            print(f"📁 {rel_path}  ({folder_i}/{len(video_folders)})")
        elif verbose >= 2:
            print(f"\n=== {rel_path} ===")

        extract_frames_from_video_folder(
            folder, output_folder=sub_output, verbose=verbose, warnings=warnings, **kwargs
        )

    if verbose >= 1:
        _clear(verbose)
        print(f"✓ Extraction terminée : {len(video_folders)} dossier(s) traité(s) → {root_output}")

    warnings.print_summary()
    _notify(sound=sound)


def _check_inputs(path, interval_s, delay_s, resize_factor):
    if not isinstance(path, str):
        raise TypeError(f"'path' doit être une chaîne, reçu {type(path).__name__}")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Chemin introuvable : {path}")
    if not isinstance(interval_s, (int, float)) or interval_s <= 0:
        raise ValueError(f"'interval_s' doit être un nombre > 0, reçu {interval_s!r}")
    if not isinstance(delay_s, (int, float)) or delay_s < 0:
        raise ValueError(f"'delay_s' doit être un nombre >= 0, reçu {delay_s!r}")
    if resize_factor is not None and not (0 < resize_factor <= 1):
        raise ValueError(f"'resize_factor' doit être compris entre 0 (exclu) et 1 (inclus), reçu {resize_factor!r}")


def extract_frames(
    path,
    interval_s=1,
    delay_s=0.5,
    resize_factor=None,
    recursive=False,
    tz="Europe/Brussels",
    exif_template_path=DEFAULT_EXIF_TEMPLATE,
    sound=True,
    verbose=1,
):
    """Point d'entrée principal de la bibliothèque.

    Args:
        path: fichier vidéo, dossier de vidéos, ou dossier racine (avec recursive=True)
        interval_s: intervalle en secondes entre deux frames extraites
        delay_s: délai en secondes avant la première frame
        resize_factor: facteur de redimensionnement (0 < x <= 1), None = taille originale
        recursive: parcourt aussi les sous-dossiers et recrée leur arborescence
        tz: fuseau horaire local du piège photo (nom IANA, ex: "Europe/Brussels")
        exif_template_path: chemin vers un template EXIF personnalisé
        sound: joue un son de fin (désactivable, utile en usage non-interactif)
        verbose: 0 = silencieux (juste les erreurs), 1 = résumé compact (défaut,
            avec effacement automatique en notebook), 2 = détaillé (comportement
            complet : liste des dossiers, avertissements au fil de l'eau, etc.)
    """
    _check_inputs(path, interval_s, delay_s, resize_factor)
    path = os.path.normpath(path)

    kwargs = dict(
        interval_s=interval_s,
        delay_s=delay_s,
        resize=resize_factor,
        tz=tz,
        exif_template_path=exif_template_path,
    )

    if os.path.isdir(path):
        if recursive:
            extract_frames_recursive(path, sound=sound, verbose=verbose, **kwargs)
        else:
            warnings = _Warnings(verbose=verbose)
            extract_frames_from_video_folder(path, verbose=verbose, warnings=warnings, **kwargs)
            if verbose >= 1:
                print(f"✓ Extraction terminée : {path}")
            warnings.print_summary()
            _notify(sound=sound)
    elif os.path.isfile(path):
        output_folder = _get_output_folder(path)
        warnings = _Warnings(verbose=verbose)
        extract_frames_from_video_file(path, output_folder, verbose=verbose, warnings=warnings, **kwargs)
        if verbose >= 1:
            print(f"✓ Extraction terminée : {path}")
        warnings.print_summary()
        _notify(sound=sound)
    else:
        raise ValueError(f"Chemin invalide ou format non supporté : {path}")

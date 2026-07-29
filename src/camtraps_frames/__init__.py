"""
camtraps_frames
================

Extraction de frames depuis des vidéos de pièges photographiques,
avec réécriture des métadonnées EXIF (date de prise de vue réelle,
lue depuis les métadonnées internes de la vidéo plutôt que le système
de fichiers).

Exemple :
    from camtraps_frames import extract_frames
    extract_frames("chemin/vers/dossier", interval_s=2, recursive=True)
"""

from .core import (
    extract_frames,
    extract_frames_from_video_file,
    extract_frames_from_video_folder,
    extract_frames_recursive,
    get_creation_time,
)

__version__ = "0.1.0"

__all__ = [
    "extract_frames",
    "extract_frames_from_video_file",
    "extract_frames_from_video_folder",
    "extract_frames_recursive",
    "get_creation_time",
]

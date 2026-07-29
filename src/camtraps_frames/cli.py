"""Interface en ligne de commande : `camtraps-frames --help`"""

import argparse
from .core import extract_frames, DEFAULT_EXIF_TEMPLATE


def build_parser():
    parser = argparse.ArgumentParser(
        prog="camtraps-frames",
        description="Extrait des frames de vidéos de pièges photographiques avec dates EXIF correctes.",
    )
    parser.add_argument("path", help="Fichier vidéo, dossier de vidéos, ou dossier racine")
    parser.add_argument("-i", "--interval", type=float, default=1.0,
                         help="Intervalle en secondes entre deux frames (défaut: 1)")
    parser.add_argument("-d", "--delay", type=float, default=0.5,
                         help="Délai en secondes avant la première frame (défaut: 0.5)")
    parser.add_argument("-r", "--resize", type=float, default=None,
                         help="Facteur de redimensionnement, ex: 0.5 pour 50%% (défaut: taille originale)")
    parser.add_argument("--recursive", action="store_true",
                         help="Parcourt aussi les sous-dossiers")
    parser.add_argument("--tz", default="Europe/Brussels",
                         help="Fuseau horaire IANA du piège photo (défaut: Europe/Brussels)")
    parser.add_argument("--exif-template", default=DEFAULT_EXIF_TEMPLATE,
                         help="Chemin vers un template EXIF .JPG personnalisé (défaut: généré automatiquement)")
    parser.add_argument("--no-sound", action="store_true",
                         help="Désactive le son de fin d'exécution")
    parser.add_argument("--verbose", type=int, choices=[0, 1, 2], default=2,
                         help="0=silencieux, 1=résumé compact, 2=détaillé (défaut en CLI: 2)")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    extract_frames(
        args.path,
        interval_s=args.interval,
        delay_s=args.delay,
        resize_factor=args.resize,
        recursive=args.recursive,
        tz=args.tz,
        exif_template_path=args.exif_template,
        sound=not args.no_sound,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()

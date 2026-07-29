# camtraps-frames

Ce programme prend tes vidéos de pièges photographiques et en extrait des
images (photos) régulièrement dans le temps — par exemple une image toutes
les 2 secondes. Chaque image reçoit automatiquement la bonne date et heure
(celle où la vidéo a réellement été filmée), ce qui te permet ensuite de
trier ou d'analyser tes images correctement dans n'importe quel logiciel de
photo (Lightroom, Photos, etc.).

Ce guide ne suppose aucune connaissance en informatique. Suis les étapes
dans l'ordre, une par une.

---

## Avant de commencer : le Terminal

Toutes les étapes ci-dessous se font dans une application qui s'appelle le
**Terminal**. C'est une fenêtre où on tape des commandes au clavier au lieu
de cliquer sur des icônes.

**Pour l'ouvrir sur Mac :**
1. Appuie sur `Cmd` + `Espace` (la loupe de recherche s'ouvre)
2. Tape `Terminal`
3. Appuie sur `Entrée`

Une fenêtre noire ou blanche avec du texte s'ouvre. C'est normal, c'est là
que tout se passe.

> 💡 Dans ce guide, chaque bloc de texte gris comme celui-ci :
> ```bash
> exemple de commande
> ```
> est une commande à **copier-coller** dans le Terminal, puis à valider avec
> la touche `Entrée`.

---

## Étape 1 — Installer les outils nécessaires

Le programme a besoin de deux choses pour fonctionner : **Python** (le
langage dans lequel il est écrit) et **ffmpeg** (un outil qui sait lire les
vidéos).

### 1.1 Vérifier si Python est déjà installé

```bash
python3 --version
```

Si tu vois quelque chose comme `Python 3.11.5`, c'est bon, passe à l'étape
suivante. Si tu vois un message d'erreur, installe Python via
[python.org/downloads](https://www.python.org/downloads/) (télécharge et
ouvre le fichier, comme n'importe quelle application).

### 1.2 Installer ffmpeg

Si tu utilises **Homebrew** (un gestionnaire de logiciels pour Mac) :
```bash
brew install ffmpeg
```

Si tu n'as jamais entendu parler de Homebrew, installe-le d'abord en
collant cette commande, puis recommence la commande `brew install ffmpeg`
juste au-dessus :
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 1.3 Vérifier que ffmpeg est bien installé

```bash
ffprobe -version
```

Tu dois voir un numéro de version s'afficher. Si tu vois une erreur, recommence
l'étape 1.2 en t'assurant qu'aucun message d'erreur n'est apparu pendant
l'installation.

---

## Étape 2 — Installer le programme camtraps-frames

Une seule commande suffit :

```bash
pip3 install git+https://github.com/qwatthez/camtraps-frames.git
```

Cette commande télécharge et installe le programme depuis internet. Elle
peut prendre une minute ou deux la première fois (elle installe aussi les
outils annexes dont le programme a besoin).

**Pour vérifier que ça a fonctionné :**
```bash
camtraps-frames --help
```

Si tu vois une liste d'options qui s'affiche (avec des mots comme `--interval`,
`--recursive`, etc.), c'est gagné, le programme est installé.

---

## Étape 3 — Utiliser le programme

Il y a deux façons de s'en servir : **en ligne de commande** (le plus
simple pour un usage ponctuel) ou **dans Jupyter** (si tu es déjà habitué à
ce logiciel).

### 3.1 En ligne de commande (recommandé pour débuter)

**Cas le plus simple : traiter toutes les vidéos d'un dossier**

```bash
camtraps-frames "/chemin/vers/ton/dossier"
```

Remplace `/chemin/vers/ton/dossier` par l'emplacement réel de ton dossier de
vidéos. Astuce : au lieu de taper le chemin à la main, tu peux **glisser le
dossier depuis le Finder directement dans la fenêtre du Terminal** — le
chemin s'écrit automatiquement.

Par exemple :
```bash
camtraps-frames "/Users/quentin/Desktop/100HUNTI"
```

**Si ton dossier contient plusieurs sous-dossiers** (un dossier par
caméra, par exemple), ajoute `--recursive` à la fin :

```bash
camtraps-frames "/Users/quentin/Desktop/100HUNTI" --recursive
```

**Résultat :** un nouveau dossier nommé `output_100HUNTI` apparaît juste à
côté de ton dossier original, contenant toutes les images extraites,
organisées de la même façon que tes vidéos.

### 3.2 Options utiles (facultatives)

Tu peux ajouter ces options à la fin de la commande, séparées par des espaces :

| Option | À quoi ça sert | Exemple |
|---|---|---|
| `--interval 2` | Extrait une image toutes les 2 secondes (par défaut : 1 seconde) | `--interval 2` |
| `--delay 0.5` | Attend 0,5 seconde avant la première image (utile si le début de la vidéo est flou) | `--delay 0.5` |
| `--resize 0.5` | Réduit la taille des images de moitié (fichiers plus légers) | `--resize 0.5` |
| `--recursive` | Traite aussi tous les sous-dossiers | — |
| `--no-sound` | N'émet pas de son à la fin du traitement | — |

**Exemple complet, tout combiné :**
```bash
camtraps-frames "/Users/quentin/Desktop/100HUNTI" --interval 2 --delay 0.5 --recursive
```

### 3.3 Dans Jupyter (si tu utilises déjà ce logiciel)

```python
from camtraps_frames import extract_frames

extract_frames(
    "/Users/quentin/Desktop/100HUNTI",
    interval_s=2,
    recursive=True
)
```

---

## Étape 4 — Comprendre ce qui s'affiche

Pendant le traitement, tu verras une ligne qui se met à jour avec le nom du
dossier en cours et sa progression, par exemple :

```
📁 cam1  (2/4)
```

Cela veut dire : "je traite le dossier `cam1`, c'est le 2ᵉ dossier sur 4 au
total".

À la toute fin, un message récapitulatif s'affiche, du type :
```
✓ Extraction terminée : 4 dossier(s) traité(s) → output_100HUNTI
```

Si certaines vidéos n'ont pas pu être traitées (fichier corrompu, format
non reconnu), un résumé des avertissements s'affiche également — ce n'est
pas grave, les autres vidéos ont bien été traitées normalement.

---

## Problèmes fréquents

**"command not found: camtraps-frames"**
Le programme n'est pas installé, ou pas dans le bon environnement. Reprends
l'étape 2.

**"command not found: ffprobe" ou "ffprobe introuvable"**
ffmpeg n'est pas installé. Reprends l'étape 1.2.

**Le Terminal affiche plein de texte rouge/orange et semble planté**
Ce n'est pas forcément une erreur bloquante — beaucoup de messages sont
juste des barres de progression qui s'affichent bizarrement. Attends que la
commande se termine (le curseur clignotant revient sur une nouvelle ligne
vide) avant de conclure qu'il y a un vrai problème.

**Rien ne se passe du tout après avoir lancé la commande**
Vérifie que le chemin du dossier est correct (recopie-le en glissant le
dossier depuis le Finder dans le Terminal, c'est plus fiable que de le
taper à la main).

**Je veux arrêter le programme en cours de route**
Clique dans la fenêtre du Terminal et appuie sur `Ctrl` + `C`.

---

## Pour aller plus loin

Ce README couvre l'usage courant. Une documentation plus technique
(paramètres avancés, utilisation en tant que bibliothèque Python, options
de journalisation) est disponible dans le fichier `README.md` du dépôt
GitHub du projet, destinée à un usage plus développeur.

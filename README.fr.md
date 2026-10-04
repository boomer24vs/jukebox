<div align="center">

<img src="docs/media/icon.png" width="96" alt="Icône Jukebox">

# Jukebox

**Un jukebox Minecraft posé sur ton bureau Linux, qui joue la musique de C418 quand tu cliques dessus.**

Un clic, un disque sort du jukebox et *Now Playing: C418 - cat* apparaît, comme dans le jeu.

![Linux](https://img.shields.io/badge/Linux-X11%20%7C%20XWayland-FCC624?logo=linux&logoColor=black)
![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![pygame-ce](https://img.shields.io/badge/pygame--ce-2.5-6AA84F)
![Licence : MIT](https://img.shields.io/badge/licence-MIT-green)

<img src="docs/media/demo.gif" width="440" alt="Le jukebox passe du mode normal au mode compact puis revient">

[English](README.md) · **Français**

</div>

---

## Fonctionnalités

- 🎵 **44 morceaux de C418** : les 12 disques et les musiques de fond, récupérés depuis *ta propre* installation de Minecraft.
- 💿 **Fidèle au jeu** : le disque sort de la fente, le message *Now Playing* est écrit avec la police de Minecraft et passe par les couleurs de l'arc-en-ciel, et des notes de musique s'échappent pendant la lecture.
- 📦 **Coffre à disques** : clique sur le petit coffre à côté du jukebox pour ouvrir un coffre Minecraft rempli de disques, un par morceau, chacun de sa couleur. Passe la souris sur un disque pour voir l'infobulle du jeu, clique dessus pour lancer ce morceau.
- 🔁 **Lecture enchaînée** : quand un morceau se termine, un autre se lance au hasard.
- 🔊 **Volume à la molette** : molette sur le jukebox. Plus c'est fort, plus les notes sont grosses et nombreuses.
- 🖱️ **Où tu veux** : fais-le glisser n'importe où sur le bureau.
- 🪟 **Un vrai widget de bureau** : fond transparent, reste sous tes applications, et les clics sur les zones vides passent à travers.
- 📏 **Mode compact** : après 10 s sans interaction, il se réduit en petit jukebox avec le titre et une barre de progression façon barre d'expérience. Passe la souris dessus pour le faire revenir.
- 🎨 **Dessiné par le code** : chaque pixel vient de `textures.py`, aucune texture du jeu n'est fournie.

<table>
<tr>
<td align="center"><img src="docs/media/normal.png" width="330" alt="Mode normal"><br><sub>Mode normal</sub></td>
<td align="center"><img src="docs/media/compact.png" width="330" alt="Mode compact"><br><sub>Mode compact</sub></td>
</tr>
<tr>
<td align="center" colspan="2"><img src="docs/media/chest.png" width="660" alt="Coffre à disques ouvert"><br><sub>Coffre à disques</sub></td>
</tr>
</table>

## Prérequis

- **Linux** avec une session X11, ou Wayland avec XWayland (le cas par défaut sur GNOME et KDE).
- **Python 3.10+**. Sur Debian/Ubuntu, installe aussi `python3-venv`.
- **Minecraft Java Edition**, lancé au moins une fois, pour que sa musique soit sur ton disque. Le launcher officiel (natif ou Flatpak) et Prism Launcher sont détectés automatiquement.
- La police gratuite **[Minecraftia](https://www.dafont.com/minecraftia.font)**.

## Installation

```bash
git clone https://github.com/boomer24vs/jukebox.git
cd jukebox
./install.sh
```

Le script :
1. crée un environnement Python dans `.venv/` et installe les dépendances ;
2. copie la musique de C418 depuis ton installation de Minecraft vers `sounds/` ;
3. vérifie la police ;
4. ajoute **Jukebox** au menu des applications.

Télécharge ensuite [Minecraftia](https://www.dafont.com/minecraftia.font) et place `Minecraftia-Regular.ttf` dans le dossier `fonts/`.

> Minecraft installé ailleurs ? Donne son dossier `assets` : `./install.sh /chemin/vers/.minecraft/assets`

## Utilisation

Lance **Jukebox** depuis le menu des applications, ou `.venv/bin/python jukebox.py`.

| Action | Effet |
|---|---|
| Clic gauche sur le jukebox | Joue un morceau au hasard (un autre clic change de morceau) |
| Clic gauche sur le petit coffre | Ouvre / ferme le coffre à disques |
| Clic gauche sur un disque du coffre | Joue ce morceau et ferme le coffre |
| Molette sur le jukebox | Volume, par pas de 10 % |
| Glisser | Déplace le jukebox |
| `Échap` | Ferme le coffre s'il est ouvert, sinon quitte |
| Clic droit sur le jukebox | Quitte |
| 10 s sans interaction | Mode compact ; passe la souris dessus pour revenir au mode normal |

## Réglages

Tout se règle dans le dictionnaire `PRESET` en haut de [`jukebox.py`](jukebox.py). Par exemple :

```python
"window_layer": "below",      # "below" (sous tes applis), "normal" ou "top" (toujours au premier plan)
"window_top_margin": 40,      # distance de départ depuis le haut de l'écran
"volume_default": 0.7,
"autoplay": True,             # un nouveau morceau au hasard se lance quand un autre se termine
"compact_delay": 10.0,        # secondes avant le mode compact
"compact_transition": 0.8,
```

## Dépannage

| Problème | Solution |
|---|---|
| `No audio file in sounds/` | Lance Minecraft Java une fois, puis `.venv/bin/python extract_music.py` |
| `No Minecraft assets found` | Donne le dossier assets : `.venv/bin/python extract_music.py /chemin/vers/assets` |
| `Font missing` | Place `Minecraftia-Regular.ttf` dans `fonts/` |
| Carré gris autour du jukebox | Ta session n'a pas de compositeur ou pas de visuel 32 bits : la transparence n'est pas disponible |
| La fenêtre ne s'ouvre pas en Wayland pur | XWayland est nécessaire (actif par défaut sur GNOME et KDE) |

Testé sur Fedora 43 avec GNOME 49 (Wayland + XWayland). Les autres bureaux devraient fonctionner mais n'ont pas encore été testés : les retours (issues) sont les bienvenus.

## Désinstallation

```bash
rm ~/.local/share/applications/jukebox.desktop
rm -rf /chemin/vers/jukebox
```

## Organisation du projet

| Fichier | Rôle |
|---|---|
| `jukebox.py` | Fenêtre, boucle principale, animations, réglages (`PRESET`) |
| `textures.py` | Pixel art généré par le code : jukebox, disques, notes, coffre et son interface |
| `player.py` | Audio : morceau au hasard ou choisi, volume, progression |
| `extract_music.py` | Copie la musique de C418 depuis ton installation de Minecraft |
| `install.sh` | Installation en une commande |

## Mentions légales

- **Ce n'est pas un produit officiel Minecraft. Il n'est ni approuvé par Mojang ou Microsoft, ni associé à eux.**
- La musique est © C418 / Mojang. Elle n'est **pas** dans ce dépôt : `extract_music.py` la copie depuis l'installation de Minecraft que tu possèdes, sur ta machine.
- La police Minecraftia est d'Andrew Tyler et n'est **pas** incluse. Télécharge-la sur dafont et vérifie sa licence là-bas.
- Le code est sous [licence MIT](LICENSE).

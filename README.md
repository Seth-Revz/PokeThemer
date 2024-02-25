PokeThemer
==========

PokeThemer is python desktop application for decompiling [PokeMMO themes](https://forums.pokemmo.com/index.php?/forum/33-client-customization/) into separate sprites, replacing the sprites, and recompiling the theme.
PokeThemer was created in hopes that it will help the community more easily create and modify themes. Along with keeping them up to date with the current client version.

## Future 

PokeThemer is a Work in Progress. Here are some things that will be worked on going forward.
- More automated way of updating themes to current client version. Each update has the potential to break themes.
- In app .xml modification/editor?


## Requirements

- [Python 3.7+](https://www.python.org/downloads/)
- [PySide6](https://pypi.org/project/PySide6/)
- [PyQtDarkTheme](https://pypi.org/project/pyqtdarktheme/)
- [Pillow](https://pypi.org/project/pillow/)

## Getting Started

Checkout the source code with `git` or download it as a .zip file.

```bash
git clone https://github.com/Seth-Revz/PokeThemer.git
cd pokethemer
pip install -r requirements.txt
python pokethemer.py
```

## Usage

1. Open a theme by selecting the themes top level folder.

    <img alt='opentheme' width=600 src='https://github.com/Seth-Revz/PokeThemer/blob/main/.github/screenshot1.png'>


2. Select and replace sprites (same size as the original).

    <img alt='replacesprite' width=600 src='https://github.com/Seth-Revz/PokeThemer/blob/main/.github/screenshot2.png'>

3. Save theme

    <img alt='savetheme' width=600 src='https://github.com/Seth-Revz/PokeThemer/blob/main/.github/screenshot3.png'>

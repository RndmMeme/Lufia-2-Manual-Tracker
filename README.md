# Lufia 2 Manual Tracker v1.4

A feature-rich manual tracker for the "Lufia 2 Ancient Cave" Randomizer (terrorwave).
Ported from the Auto-Tracker codebase to provide advanced UI features for manual users.

## Features
- **Advanced UI**: customizable Docking interface (Draggable/Floatable panels).
- **Map Visualization**: 
    - Auto-scaling map with accessibility logic (Red/Green/Grey dots).
    - Draggable Character Sprites to mark found party members.
    - Context menus for location management.
- **Inventory/Logic**: 
    - Smart logic engine that calculates accessibility based on your item/spell inventory.
    - Item search for City shops.
- **Customization**:
    - "Edit -> Edit Layout" mode to rearrange icons freely.
    - Dark Theme enabled by default.
    - Persistent settings (Window state, layout, colors).

## Installation
1. Install Python 3.10+.
2. Install dependencies: `pip install -r requirements.txt` (PyQt6).
3. Run `src/main.py`.

## Usage
- **Left-Click** map dots to cycle their state manually.
- **Right-Click** map dots to assign characters or check shops.
- **Click** inventory items to toggle them.
- **Click** Character icons:
    - 1x: Marked as Obtained (Half Opacity).
    - 2x: Marked as Active Party (Full Opacity).
    - 3x: Reset.

## Credits
- **RndmMeme**: Original Auto Tracker & Port.
- **abyssonym**: Lufia 2 Randomizer.

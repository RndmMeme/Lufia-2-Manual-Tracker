# Lufia 2 Manual Tracker v1.4.3

A feature-rich manual tracker for the "Lufia 2 Ancient Cave" Randomizer (terrorwave).
Ported from the Auto-Tracker codebase to provide advanced UI features for manual users.

## ✨ New in v1.4.3
*   **Custom Map Shapes**: You can now define individual map dot shapes for **Cities** and **Dungeons**.
*   **City Color Overrides**: Specify custom colors for unexplored cities, bypassing the default red/green logic.
*   **Layout Recovery**: Added **"Reset Picture Positions"** to quickly restore icon locations to a default.
*   **Instant Tooltips**: Map dot mouse-over delays have been eliminated for lightning-fast location hunting.
*   **Items / Spells Add Feature**: Added the ability to assign found Items and Spells to cities via the `Items / Spells` interface.
*   **Adjustable Logic Rules**: Narvick access rules properly require "Engine" only (formerly allowed "Jade").

## Features
- **Advanced UI**: customizable Docking interface (Draggable/Floatable panels).
- **Map Visualization**: 
    - Auto-scaling map with accessibility logic (Red/Green/Grey dots).
    - Draggable Character Sprites to mark found party members.
    - Context menus for location management.
- **Inventory/Logic**: 
    - Smart logic engine that calculates accessibility based on your item/spell inventory.
    - Item search for City shops (via Add button on Items panel).
- **Customization**:
    - "Custom -> Edit Layout" mode to rearrange icons freely.
    - Dark Theme enabled by default.
    - Persistent settings (Window state, layout, colors).

## Installation
1. Install Python 3.10+.
2. Install dependencies: `pip install -r requirements.txt` (PyQt6).
3. Run `src/main.py`.

## Usage
- **Left-Click** map dots to cycle their state manually.
- **Right-Click** map dots to assign characters to dungeons. Use `Add` on the Items panel for shops.
- **Click** inventory items to toggle them.
- **Click** Character icons:
    - 1x: Marked as Obtained (Half Opacity).
    - 2x: Marked as Active Party (Full Opacity).
    - 3x: Reset.

## Credits
- **RndmMeme**: Original Auto Tracker & Port.
- **abyssonym**: Lufia 2 Randomizer.

from PyQt6.QtCore import QObject, pyqtSignal, QPointF
import json
import logging
from typing import Dict, Any, Optional

class StateManager(QObject):
    """
    Central repository for the application state.
    Handles manual overrides and toroidal world logic.
    """
    
    # Signals for UI updates
    inventory_changed = pyqtSignal(dict)  # Emits full inventory dict
    location_changed = pyqtSignal(str, str)  # location_name, new_state (red/green/grey)
    player_position_changed = pyqtSignal(float, float)  # x, y (canvas coordinates)
    character_changed = pyqtSignal(str, bool)  # name, is_obtained
    character_assigned = pyqtSignal(str, str) # location, character_name
    character_unassigned = pyqtSignal(str, str) # location, character_name
    
    reset_occurred = pyqtSignal() # New signal for global reset
    
    shop_items_changed = pyqtSignal(list) # List of {location, name} dictionaries
    hints_changed = pyqtSignal(str)
    
    def __init__(self, logic_engine):
        super().__init__()
        self.logic_engine = logic_engine
        
        # --- Internal State ---
        self._inventory: Dict[str, bool] = {}
        self._locations: Dict[str, str] = {}  # name -> state
        self._characters: Dict[str, bool] = {}
        self._character_locations: Dict[str, str] = {}
        self._active_party = set()
        self._active_party_list = [] # Ordered list for Sprite Display
        self._obtained_capsules = set()
        self._player_pos = QPointF(0, 0)
        self._game_world_size = (4096, 4096)  # Standard SNES Map Size
        self._canvas_size = (400, 400)        # Fixed Canvas Size
        self.shop_items = [] # List of {location, name}
        self.hints_text = ""
        
        # --- Overrides ---
        # If a user manually clicks something, it gets locked here.
        self._manual_inventory_overrides: Dict[str, bool] = {}
        self._manual_location_overrides: Dict[str, str] = {}
        self._manual_character_overrides: Dict[str, bool] = {}
        
        # --- Load Location Mapping ---
        try:
             import os
             import sys
             
             # Robust path finding
             if getattr(sys, 'frozen', False):
                 base_path = sys._MEIPASS
                 mapping_path = os.path.join(base_path, "src", "data", "location_name_mapping.json")
             else:
                 # Calculate path relative to this file (src/core/state_manager.py) -> src/data is up one level then down
                 # current_dir = src/core
                 current_dir = os.path.dirname(os.path.abspath(__file__))
                 # up one level -> src
                 src_dir = os.path.dirname(current_dir)
                 mapping_path = os.path.join(src_dir, "data", "location_name_mapping.json")

             with open(mapping_path, 'r') as f:
                 self._location_mapping = json.load(f)
             logging.info(f"Loaded {len(self._location_mapping)} location mappings.")
        except Exception as e:
            logging.error(f"Failed to load location mapping: {e}")
            self._location_mapping = {}

    def _normalize_location_name(self, raw_loc):
        """
        Normalize location name from spoiler log using loaded mapping.
        Replicates v1.3 Logic: Linear search to find FIRST matching internal name.
        """
        if not raw_loc:
            return "Unknown"
            
        # Linear search for FIRST match (Value == raw_loc)
        for internal_name, spoiler_name in self._location_mapping.items():
            if spoiler_name == raw_loc:
                return internal_name
                
        return raw_loc
        
    # --- Public Accessors ---
    
    def get_inventory(self) -> Dict[str, bool]:
        """Explicit getter for inventory."""
        effective = self._inventory.copy()
        effective.update(self._manual_inventory_overrides)
        return effective

    @property
    def inventory(self) -> Dict[str, bool]:
        """Returns effective inventory (actual + overrides)."""
        return self.get_inventory()

    @property
    def locations(self) -> Dict[str, str]:
        """Returns effective location states."""
        effective = self._locations.copy()
        effective.update(self._manual_location_overrides)
        return effective
        
    def get_player_position(self) -> QPointF:
        """Returns current player position (canvas coordinates)."""
        return self._player_pos

    # --- Manual Interactions (High Priority) ---
    
    def set_manual_location_state(self, name: str, state: str):
        """User manually clicked a location dot."""
        self._manual_location_overrides[name] = state
        self.location_changed.emit(name, state)
        logging.info(f"Manual override: Location {name} -> {state}")

    def toggle_manual_inventory(self, item_name: str):
        """User clicked an item icon."""
        current = self.inventory.get(item_name, False)
        new_state = not current
        self._manual_inventory_overrides[item_name] = new_state
        self.inventory_changed.emit(self.inventory)
        logging.info(f"Manual override: Item {item_name} -> {new_state}")

    def reset_overrides(self):
        """Clears all manual overrides, reverting to raw external data."""
        self._manual_inventory_overrides.clear()
        self._manual_location_overrides.clear()
        self._manual_character_overrides.clear()
        
        # Re-emit everything to sync UI
        self.inventory_changed.emit(self._inventory)
        for loc, state in self._locations.items():
            self.location_changed.emit(loc, state)
        # TODO: emit characters
        
        logging.info("Manual overrides reset.")

    # --- External Data Updates (Low Priority) ---
    
    # [Removed Auto-Tracking External Updates]

    def _update_player_position(self, game_x: int, game_y: int):
        """
        Calculates canvas position from game coordinates.
        Handles toroidal wrapping visuals if necessary (though straight mapping is usually fine for a 1:1 map).
        """
        # 1. Scale to Canvas
        scale_x = self._canvas_size[0] / self._game_world_size[0]
        scale_y = self._canvas_size[1] / self._game_world_size[1]
        
        canvas_x = game_x * scale_x
        canvas_y = game_y * scale_y
        
        self._player_pos = QPointF(canvas_x, canvas_y)


    @property
    def obtained_characters(self) -> Dict[str, bool]:
        """Returns all obtained characters (whether in party or not)."""
        return self._characters.copy()

    @property
    def active_party(self) -> set:
        """Returns the set of characters currently in the player's party."""
        return getattr(self, '_active_party', set())

    def get_active_party_leader(self) -> Optional[str]:
        """Returns the name of the first character in the active party (Slot 1)."""
        if hasattr(self, '_active_party_list') and self._active_party_list:
             return self._active_party_list[0]
        return None
        
    def get_character_at_location(self, location_name: str) -> Optional[str]:
        return self._character_locations.get(location_name)

    def set_character_obtained(self, name: str, obtained: bool):
        self._characters[name] = obtained
        self.character_changed.emit(name, obtained)
        
    def assign_character_to_location(self, location: str, character_name: str):
        # 0. Prevent Redundant Updates
        if self._character_locations.get(location) == character_name:
            return

        # 1. Check if character is already assigned elsewhere (Move)
        prev_loc = None
        for loc, name in self._character_locations.items():
            if name == character_name:
                prev_loc = loc
                break
        
        if prev_loc:
             # Remove from old location, but keep obtained status (moving)
             # Just emit unassign so map sprite is removed
             del self._character_locations[prev_loc]
             self.character_unassigned.emit(prev_loc, character_name)

        # 2. Check if location already has someone (Overwrite)
        old_char = self._character_locations.get(location)
        if old_char and old_char != character_name:
             # User says: "Previous character needs to be dimmed" (Reset)
             self.set_character_obtained(old_char, False)
             self.character_unassigned.emit(location, old_char)
             
        # 3. Assign
        self._character_locations[location] = character_name
        self.set_character_obtained(character_name, True)
        
        # 4. Mark Location as "Cleared"
        self.set_manual_location_state(location, "cleared")
        
        # Emit signal for MapWidget
        self.character_assigned.emit(location, character_name)
        
    def remove_character_assignment(self, location: str):
        char = self._character_locations.pop(location, None)
        if char:
            # Logic Parity v1.3: "Removes from inactive but obtained roster"
            # Since inactive roster = obtained=True but not in Active Party,
            # we set obtained=False.
            self.set_character_obtained(char, False)
            self.character_unassigned.emit(location, char)
            logging.info(f"StateManager: Removed {char} from {location} and set to Not Obtained.")

    def register_shop_item(self, location, item_name):
        # Check duplicate
        for entry in self.shop_items:
            if entry['location'] == location and entry['name'] == item_name:
                return
        self.shop_items.append({'location': location, 'name': item_name})
        self.shop_items_changed.emit(self.shop_items)
        
    def unregister_shop_item(self, location, item_name):
        self.shop_items = [e for e in self.shop_items if not (e['location'] == location and e['name'] == item_name)]
        self.shop_items_changed.emit(self.shop_items)
        
    def clear_shop_items(self):
        self.shop_items = []
        self.shop_items_changed.emit(self.shop_items)

    def update_hints(self, text):
        if self.hints_text != text:
             self.hints_text = text
             self.hints_changed.emit(text)

    # [Removed toggle_auto_tracking, on_helper_data, process_auto_update]

    def reset_state(self):
        """Reset all tracker state to defaults (but keep options)."""
        logging.info("Resetting tracker state to defaults.")
        self._inventory = {}
        self._characters = {}
        self._active_party = set()
        self._obtained_capsules = set()
        
        self.reset_overrides()
        
        # Unassign all map sprites explicitly
        for loc, char in list(self._character_locations.items()):
            self.character_unassigned.emit(loc, char)
        self._character_locations = {}
        
        # Locations reset
        self._locations = {}
        self.location_changed.emit("Reset", "reset") 
        
        # Emit all signals to clear UI
        self.inventory_changed.emit({})
        self.clear_shop_items()
        
        self.hints_text = ""
        # hints UI cleared by MainWindow._on_reset_occurred
        
        # Characters:
        for name in ["Maxim", "Selan", "Guy", "Artea", "Tia", "Dekar", "Lexis", "Jelze", "Flash", "Gusto", "Zeppy", "Darbi", "Sully", "Blaze"]:
            self.character_changed.emit(name, False)
        
        self.player_position_changed.emit(0, 0)
        
        self.reset_occurred.emit()



    def register_spoiler_location(self, location: str, character_name: str):
        """
        Registers a potential character location from the spoiler log.
        Does NOT mark as obtained or cleared.
        """
        # Update internal map
        self._character_locations[location] = character_name
        # Emit signal so MapWidget can place the sprite (if location not cleared)
        self.character_assigned.emit(location, character_name)

    # [Removed process_spoiler_log, update_capsule_sprites]

    def save_state(self, filepath: str):
        """Serialize current overrides AND progress to JSON."""
        data = {
            "inventory_overrides": self._manual_inventory_overrides,
            "location_overrides": self._manual_location_overrides,
            "character_locations": self._character_locations,
            # Full State
            "inventory": self._inventory,
            "locations": self._locations,
            "characters": self._characters,
            "active_party": list(self._active_party),
            "obtained_capsules": list(self._obtained_capsules),
            "shop_items": self.shop_items,
            "hints": self.hints_text
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        logging.info(f"State saved to {filepath}")

    def load_state(self, filepath: str):
        """Load state from JSON and apply."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self._manual_inventory_overrides = data.get("inventory_overrides", {})
        self._manual_location_overrides = data.get("location_overrides", {})
        
        # Restore State
        self._inventory = data.get("inventory", {})
        self._locations = data.get("locations", {})
        self._characters = data.get("characters", {})
        self._character_locations = data.get("character_locations", {})
        
        self.shop_items = data.get("shop_items", [])
        self.shop_items_changed.emit(self.shop_items)
        
        self.hints_text = data.get("hints", "")
        self.hints_changed.emit(self.hints_text)
        
        self._active_party = set(data.get("active_party", []))
        self._obtained_capsules = set(data.get("obtained_capsules", []))
        
        # Re-emit changes
        self.inventory_changed.emit(self.inventory)
        for loc, state in self._locations.items():
            self.location_changed.emit(loc, state)
        
        # We need to re-emit character assignments essentially to place sprites
        for loc, char in self._character_locations.items():
             self.character_assigned.emit(loc, char)
            
        # Also emit character toggles
        for char, obtained in self._characters.items():
            self.character_changed.emit(char, obtained)
            
        logging.info(f"State loaded from {filepath}")

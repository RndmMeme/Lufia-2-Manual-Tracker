from PyQt6.QtCore import QObject, pyqtSignal, QPointF
import json
import logging
from typing import Dict, Any, Optional

class StateManager(QObject):
    """
    Central repository for the application state.
    Handles manual overrides, data sync, and toroidal world logic.
    """
    
    # Signals for UI updates
    inventory_changed = pyqtSignal(dict)  # Emits full inventory dict
    location_changed = pyqtSignal(str, str)  # location_name, new_state (red/green/grey)
    player_position_changed = pyqtSignal(float, float)  # x, y (canvas coordinates)
    character_changed = pyqtSignal(str, bool)  # name, is_obtained
    character_assigned = pyqtSignal(str, str) # location, character_name
    character_unassigned = pyqtSignal(str, str) # location, character_name
    
    # Signal for external auto-updates (from network)
    auto_update_received = pyqtSignal(dict) # payload
    
    def __init__(self, logic_engine):
        super().__init__()
        self.logic_engine = logic_engine
        
        # --- Internal State ---
        self._inventory: Dict[str, bool] = {}
        self._locations: Dict[str, str] = {}  # name -> state
        self._characters: Dict[str, bool] = {}
        self._character_locations: Dict[str, str] = {}
        self._player_pos = QPointF(0, 0)
        self._game_world_size = (4096, 4096)  # Standard SNES Map Size
        self._canvas_size = (400, 400)        # Fixed Canvas Size
        
        # --- Overrides ---
        # If a user manually clicks something, it gets locked here.
        # External data updates for locked items are ignored until reset.
        self._manual_inventory_overrides: Dict[str, bool] = {}
        self._manual_location_overrides: Dict[str, str] = {}
        self._manual_character_overrides: Dict[str, bool] = {}
        
    # --- Public Accessors ---
    
    @property
    def inventory(self) -> Dict[str, bool]:
        """Returns effective inventory (actual + overrides)."""
        effective = self._inventory.copy()
        effective.update(self._manual_inventory_overrides)
        return effective

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
    
    def update_from_external(self, data: Dict[str, Any]):
        """
        Ingest data from the C# helper.
        Expected keys: 'inventory', 'cleared_locations', 'player_x', 'player_y'
        """
        # 1. Update Inventory
        if 'inventory' in data:
            raw_inventory = data['inventory']
            # Only update internal state, do not overwrite overrides
            self._inventory = raw_inventory
            # Emit key-by-key or full update? Full update is safer for UI consistency
            self.inventory_changed.emit(self.inventory)

        # 2. Update Locations
        # Logic is complex here: 'cleared_locations' comes from memory (grey).
        # Accessibility (red/green) is calculated by LogicEngine (not handled here, but triggered by inv change).
        # This method mainly updates the "Cleared" status from game memory.
        if 'cleared_locations' in data:
            for loc in data['cleared_locations']:
                if loc not in self._manual_location_overrides:
                    self._locations[loc] = "cleared"
                    self.location_changed.emit(loc, "cleared")

        # 3. Update Player Position (Toroidal Wrap Logic)
        if 'player_x' in data and 'player_y' in data:
            new_game_x = data['player_x']
            new_game_y = data['player_y']
            self._update_player_position(new_game_x, new_game_y)

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
        
        # 2. Toroidal Check (Optional visual smoothing)
        # If the player jumps from 0 to 4096, we might want to suppress animation trails?
        # For a simple dot update, absolute positioning is fine.
        
        # 2. Toroidal Check (Optional visual smoothing)
        # If the player jumps from 0 to 4096, we might want to suppress animation trails?
        # For a simple dot update, absolute positioning is fine.
        
        self._player_pos = QPointF(canvas_x, canvas_y)

    # --- Tracking Options (Granular Filters) ---
    def update_tracking_options(self, options: dict):
        """
        Updates the filter mask for auto-tracking.
        Expected keys: 'chars', 'tools', 'keys', 'maidens', 'pos' (all bools).
        """
        self._tracking_options = options
        logging.info(f"Tracking options updated: {options}")

    def _is_tracking_enabled(self, category: str) -> bool:
        """Returns True if the category is enabled in tracking options (default True)."""
        if not hasattr(self, '_tracking_options'):
             return True # Default allow all if not set
        return self._tracking_options.get(category, True)


    @property
    def active_characters(self) -> Dict[str, bool]:
        return self._characters.copy()
        
    def get_character_at_location(self, location_name: str) -> Optional[str]:
        return self._character_locations.get(location_name)

    def set_character_obtained(self, name: str, obtained: bool):
        self._characters[name] = obtained
        self.character_changed.emit(name, obtained)
        
    def assign_character_to_location(self, location: str, character_name: str):
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
            # Should we mark char as not obtained? v1.3 toggles toggle logic.
            # v1.3 `remove_character_location` sets `manual_toggles[char] = False` (Inactivates char).
            self.set_character_obtained(char, False)
            self.character_unassigned.emit(location, char)

    def process_auto_update(self, payload: dict):
        """
        Process data received from external tracker.
        Payload e.g.: {"inventory": ["Bomb", "Arrow"], "location": "Alunze", "cleared_locations": [], "player_x": 100, "player_y": 100}
        """
        # Inventory (split into Tools/Keys?) 
        # For simplicity, if 'tools' or 'keys' is disabled, we might want to filter specific item names?
        # But commonly "inventory" is just one blob. 
        # Let's assume 'tools' covers general inventory for now or check granular flags if we can categorize items.
        # Since we don't map every item to a category here easily without data loader, 
        # we will use 'tools' as the master switch for Inventory updates for now, 
        # or separate if the payload separates them.
        
        # Current implementation assumes monolithic "inventory".
        # Let's check 'tools' flag for basic items.
        if self._is_tracking_enabled('tools') and "inventory" in payload:
            raw_inventory = payload['inventory']
            # Only update internal state, do not overwrite overrides
            self._inventory = raw_inventory
            self.inventory_changed.emit(self.inventory)
        
        # Locations (Cleared)
        # We don't have a specific "locations" checkbox? v1.3 had "Keys"? 
        # Actually v1.3 had "Keys", which likely implied Dungeon Keys.
        # "All", "Chars", "Tools", "Keys", "Maidens", "Pos".
        # Let's map "Keys" to cleared_locations/dungeons? Or actual Key items?
        # Assuming "Keys" means Scenario Items (Key Items).
        # We will filter inventory updates based on item type if possible, or just allow all if 'tools' OR 'keys' is on.
        
        # Player Position
        if self._is_tracking_enabled('pos') and 'player_x' in payload and 'player_y' in payload:
             new_game_x = payload['player_x']
             new_game_y = payload['player_y']
             self._update_player_position(new_game_x, new_game_y)
             self.player_position_changed.emit(self._player_pos.x(), self._player_pos.y())
        
        # Cleared Locations (No direct mapping in checkboxes, maybe 'keys' or 'tools'?)
        # Let's allow it if 'tools' is on, as it affects accessibility.
        if self._is_tracking_enabled('tools') and 'cleared_locations' in payload:
             for loc in payload['cleared_locations']:
                if loc not in self._manual_location_overrides:
                    self._locations[loc] = "cleared"
                    self.location_changed.emit(loc, "cleared")

        # Emit signal for logging/debug
        self.auto_update_received.emit(payload)

    def save_state(self, filepath: str):
        """Serialize current overrides to JSON."""
        data = {
            "inventory_overrides": self._manual_inventory_overrides,
            "location_overrides": self._manual_location_overrides,
            "character_locations": self._character_locations,
            "character_obtained": self._characters
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
        self._character_locations = data.get("character_locations", {})
        self._characters = data.get("character_obtained", {})
        
        # Re-emit changes
        self.inventory_changed.emit(self.inventory)
        for loc, state in self._locations.items():
            self.location_changed.emit(loc, state)
        
        # We need to re-emit character assignments essentially to place sprites
        # This is tricky because `character_assigned` is single event.
        # But `MainWindow` handles restoring sprites on full refresh?
        # No, `MainWindow` adds sprite only on signal `character_assigned`.
        # We need to manually re-emit assignments efficiently.
        # Or have MainWindow clear sprites and reload from state.
        # Let's emit signals.
        
        # Clear existing sprites? MainWindow doesn't have "clear all sprites" method exposed easily
        # inside `load_state`. 
        # But we can iterate known locations and emit.
        
        for loc, char in self._character_locations.items():
            self.character_assigned.emit(loc, char)
            
        # Also emit character toggles
        for char, obtained in self._characters.items():
            self.character_changed.emit(char, obtained)
            
        logging.info(f"State loaded from {filepath}")


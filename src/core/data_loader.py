import json
import logging
from pathlib import Path
from typing import Dict, Any
from utils.constants import DATA_DIR, IMAGES_DIR

class DataLoader:
    """
    Handles loading of static data (JSONs) and resources.
    Caches data to avoid redundant IO.
    """
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        
    def load_json(self, filename: str) -> Dict[str, Any]:
        """Loads a JSON file from the data directory."""
        if filename in self._cache:
            return self._cache[filename]
            
        path = DATA_DIR / filename
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._cache[filename] = data
                return data
        except FileNotFoundError:
            logging.error(f"File not found: {path}")
            return {}
        except json.JSONDecodeError as e:
            logging.error(f"JSON Decode Error in {path}: {e}")
            return {}

    def get_locations(self) -> Dict[str, Any]:
        return self.load_json("locations.json")

    def get_locations_logic(self) -> Dict[str, Any]:
        return self.load_json("locations_logic.json")

    def get_cities(self) -> Dict[str, Any]:
        return self.load_json("cities.json")

    def get_items_spells(self) -> Dict[str, Any]:
        return self.load_json("items_spells.json")
        
    def get_tool_items(self) -> Dict[str, Any]:
        return self.load_json("tool_items.json")

    def resolve_image_path(self, relative_path: str) -> str:
        """Resolves a relative image path to an absolute system path."""
        full_path = IMAGES_DIR / relative_path
        return str(full_path)

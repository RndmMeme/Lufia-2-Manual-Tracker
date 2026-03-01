import json
import os
import logging
from PyQt6.QtCore import QObject, QPoint
from utils.constants import DATA_DIR

class LayoutManager(QObject):
    """
    Manages the saving and loading of widget positions within their containers.
    """
    def __init__(self):
        super().__init__()
        self.config_path = DATA_DIR / "layout_config.json"
        self.default_config_path = DATA_DIR / "default_layout_config.json"
        self._layouts = {}
        self.load_layout()

    def load_layout(self):
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    self._layouts = json.load(f)
                logging.info("Layout config loaded.")
            except Exception as e:
                logging.error(f"Failed to load layout config: {e}")
                self._layouts = {}
        else:
            self._layouts = {}

    def save_layout(self):
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self._layouts, f, indent=4)
            logging.info("Layout config saved.")
        except Exception as e:
            logging.error(f"Failed to save layout config: {e}")

    def save_custom_as_default(self):
        try:
            with open(self.default_config_path, 'w') as f:
                json.dump(self._layouts, f, indent=4)
            logging.info("Saved current layout as default.")
        except Exception as e:
            logging.error(f"Failed to save default layout config: {e}")

    def reset_to_default(self):
        if self.default_config_path.exists():
            try:
                with open(self.default_config_path, 'r') as f:
                    self._layouts = json.load(f)
                logging.info("Restored default layout config.")
            except Exception as e:
                logging.error(f"Failed to load default layout: {e}")
                self._layouts = {}
        else:
            self._layouts = {}
            logging.info("No default layout config found. Reset to empty.")
        self.save_layout()

    def get_position(self, widget_id: str, item_name: str) -> tuple:
        """Returns (x, y) or None if not found."""
        container = self._layouts.get(widget_id, {})
        pos = container.get(item_name)
        if pos:
            return (pos['x'], pos['y'])
        return None

    def set_position(self, widget_id: str, item_name: str, x: int, y: int):
        if widget_id not in self._layouts:
            self._layouts[widget_id] = {}
        
        self._layouts[widget_id][item_name] = {'x': x, 'y': y}
        self.save_layout() # Auto-save on change? Or explicit save? Auto-save is easier for user.

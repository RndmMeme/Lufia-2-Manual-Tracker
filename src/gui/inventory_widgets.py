from PyQt6.QtWidgets import QWidget, QVBoxLayout
from .widgets.item_grid import ItemGrid
from utils.constants import IMAGES_DIR

class ToolsWidget(QWidget):
    def __init__(self, data_loader, layout_manager, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        
        # tool_items.json contains 7 items. User wants straight left-to-right.
        # columns=7 forces a single row if width allows.
        data = data_loader.load_json("tool_items.json")
        
        self.grid = ItemGrid(data, IMAGES_DIR, "tools", layout_manager, icon_size=40)
        self.layout.addWidget(self.grid)
        self.layout.addStretch()

    # ... connect_signals ...
    def connect_signals(self, state_manager):
        self.grid.item_clicked.connect(state_manager.toggle_manual_inventory)
        state_manager.inventory_changed.connect(self._on_inventory_changed)

    def _on_inventory_changed(self, inventory):
        for name, state in inventory.items():
            self.grid.set_item_state(name, state)
            
    def set_content_font_size(self, size):
        self.grid.set_content_font_size(size)

    def set_edit_mode(self, enabled):
        self.grid.set_edit_mode(enabled)


class ScenarioWidget(QWidget):
    def __init__(self, data_loader, layout_manager, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        
        data = data_loader.load_json("scenario_items.json")
        
        # Filter out unwanted keys
        # User request: remove "Door Key" and "Shrine" (actually "Shrine" might be "Shrine key"?)
        # Keys in json are: "Door key", "Shrine", "Basement", etc.
        filtered_data = {
            k: v for k, v in data.items() 
            if k not in ["Door key", "Shrine"]
        }
        
        self.grid = ItemGrid(filtered_data, IMAGES_DIR, "keys", layout_manager, icon_size=40, show_labels=True)
        self.layout.addWidget(self.grid)
        self.layout.addStretch()

    def connect_signals(self, state_manager):
        self.grid.item_clicked.connect(state_manager.toggle_manual_inventory)
        state_manager.inventory_changed.connect(self._on_inventory_changed)

    def _on_inventory_changed(self, inventory):
        for name, state in inventory.items():
            self.grid.set_item_state(name, state)

    def set_content_font_size(self, size):
        self.grid.set_content_font_size(size)

    def set_edit_mode(self, enabled):
        self.grid.set_edit_mode(enabled)

    def connect_signals(self, state_manager):
        self.grid.item_clicked.connect(state_manager.toggle_manual_inventory)
        state_manager.inventory_changed.connect(self._on_inventory_changed)

    def _on_inventory_changed(self, inventory):
        for name, state in inventory.items():
            self.grid.set_item_state(name, state)

    def set_content_font_size(self, size):
        self.grid.set_content_font_size(size)

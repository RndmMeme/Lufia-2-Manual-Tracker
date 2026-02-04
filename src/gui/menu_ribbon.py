from PyQt6.QtWidgets import QMenuBar, QMenu, QWidget, QHBoxLayout
from PyQt6.QtGui import QAction
from PyQt6.QtCore import pyqtSignal
from .help_dialogs import HelpDialog, AboutDialog

class MenuRibbon(QWidget):
    """
    Replicates the v1.4 Menu Ribbon (Manual Mode).
    Wraps a QMenuBar and a Custom Panel in a QHBoxLayout to control positioning.
    """
    # Signals
    reset_requested = pyqtSignal()
    save_requested = pyqtSignal()
    load_requested = pyqtSignal()
    
    # Customization Signals
    player_color_requested = pyqtSignal()
    player_shape_requested = pyqtSignal(str)
    player_size_requested = pyqtSignal(float)
    sprite_visibility_toggled = pyqtSignal(str, bool) # category, visible
    font_adj_toggled = pyqtSignal(bool)
    header_color_requested = pyqtSignal()
    edit_layout_toggled = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Main Layout
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self.setLayout(layout)
        
        # --- Internal Menu Bar ---
        self.menu_bar = QMenuBar()
        self.menu_bar.setStyleSheet("""
            QMenuBar {
                background-color: #2b2b2b;
                color: #ffffff;
                border: none;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 4px 10px;
                margin: 2px;
            }
            QMenuBar::item:selected {
                background-color: #3d3d3d;
            }
            QMenu {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #3d3d3d;
            }
            QMenu::item:selected {
                background-color: #3d3d3d;
            }
        """)
        # We need to ensure the menu bar doesn't expand infinitely if we want stuff next to it.
        self.menu_bar.setSizePolicy(self.menu_bar.sizePolicy().horizontalPolicy(), self.menu_bar.sizePolicy().verticalPolicy())
        layout.addWidget(self.menu_bar)

        # --- Options (Left) ---
        options_menu = self.menu_bar.addMenu("Options")
        options_menu.addAction("Reset", self.reset_requested.emit)
        options_menu.addAction("Save", self.save_requested.emit)
        options_menu.addAction("Load", self.load_requested.emit)
        
        # --- Custom (Middle) ---
        custom_menu = self.menu_bar.addMenu("Edit")
        
        # Layout & Visuals
        self.font_adj_action = QAction("Show Font Adj", self)
        self.font_adj_action.setCheckable(True)
        self.font_adj_action.toggled.connect(self.font_adj_toggled.emit)
        custom_menu.addAction(self.font_adj_action)
        
        self.edit_layout_action = QAction("Edit Layout", self)
        self.edit_layout_action.setCheckable(True)
        self.edit_layout_action.toggled.connect(self.edit_layout_toggled.emit)
        custom_menu.addAction(self.edit_layout_action)
        
        custom_menu.addAction("Header Color", self.header_color_requested.emit)
        
        custom_menu.addSeparator()
        
        # Player Marker
        # custom_menu.addAction("Player Color (Manual)", self.player_color_requested.emit)
        
        # Removed Player Shape/Size menus as requested for manual tracker simplification
        # (Users can still set color for the basic dot)

        # Show Sprites Submenu
        sprite_menu = QMenu("Show Sprites", self)
        
        self.sprite_actions = {}
        for cat in ["All", "Chars", "Capsules", "Maidens"]:
            action = QAction(cat, self)
            action.setCheckable(True)
            action.setChecked(True)
            # Use lower case for internal keys
            action.toggled.connect(lambda checked, c=cat.lower(): self.sprite_visibility_toggled.emit(c, checked))
            if cat == "All":
                 action.toggled.connect(self._on_all_sprites_toggled)
            self.sprite_actions[cat] = action
            sprite_menu.addAction(action)
            
        custom_menu.addMenu(sprite_menu)
        
        # --- Help / About (Right of Custom) ---
        about_action = self.menu_bar.addAction("About")
        about_action.triggered.connect(self._show_about)
        
        help_action = self.menu_bar.addAction("Help") 
        help_action.triggered.connect(self._show_help)
        
        layout.addStretch()
        
        # Overall Styling
        self.setStyleSheet("background-color: #2b2b2b;")

    def _show_about(self):
        dlg = AboutDialog(self)
        dlg.exec()
        
    def _show_help(self):
        dlg = HelpDialog(self)
        dlg.exec()

    def _on_all_sprites_toggled(self, checked):
        for k, action in self.sprite_actions.items():
            if k != "All":
                action.setChecked(checked)

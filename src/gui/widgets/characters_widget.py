from PyQt6.QtWidgets import QWidget, QGridLayout, QLabel, QVBoxLayout, QFrame, QScrollArea
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QPoint
from PyQt6.QtGui import QDrag, QPixmap, QPainter, QColor

class DraggableLabel(QLabel):
    clicked_signal = pyqtSignal()
    
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.name = name
        self.setFixedSize(40, 40)
        self.setScaledContents(True)

    def mousePressEvent(self, event):
        # We need to know if parent is in edit mode.
        # Parent hierarchy: CharacterCell -> CharactersCanvas -> ScrollAreaViewport -> ScrollArea -> CharactersWidget?
        # Actually: CharacterCell -> CharactersCanvas
        parent = self.parentWidget().parentWidget() # Get Canvas
        if parent and hasattr(parent, 'edit_mode') and parent.edit_mode:
             event.ignore() 
        else:
             # Check direct parent too just in case
             direct_parent = self.parentWidget()
             if direct_parent and hasattr(direct_parent, 'edit_mode') and direct_parent.edit_mode:
                  event.ignore()
             else:
                if event.button() == Qt.MouseButton.LeftButton:
                    self.drag_start_position = event.pos()
                super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # Assignment Drag (Edit Mode OFF)
        # Check parents for edit mode
        p = self.parentWidget()
        canvas = p.parentWidget() if p else None
        
        is_edit = False
        if p and hasattr(p, 'edit_mode') and p.edit_mode: is_edit = True
        if canvas and hasattr(canvas, 'edit_mode') and canvas.edit_mode: is_edit = True
            
        if is_edit:
            event.ignore()
            return

        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if (event.pos() - self.drag_start_position).manhattanLength() < 10:
            return

        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self.name)
        drag.setMimeData(mime_data)
        
        pixmap = self.pixmap()
        if pixmap:
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.pos())

        drag.exec(Qt.DropAction.CopyAction | Qt.DropAction.MoveAction)
        
    def mouseReleaseEvent(self, event):
        p = self.parentWidget()
        canvas = p.parentWidget() if p else None
        
        is_edit = False
        if p and hasattr(p, 'edit_mode') and p.edit_mode: is_edit = True
        if canvas and hasattr(canvas, 'edit_mode') and canvas.edit_mode: is_edit = True
        
        if is_edit:
            event.ignore()
            return
            
        self.clicked_signal.emit()
        super().mouseReleaseEvent(event)

class CharacterCell(QWidget):
    """
    Compound widget: Icon + Name Label + Location Label
    """
    clicked = pyqtSignal(str)
    
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.name = name
        self.setFixedSize(60, 60) # Increased size for label space
        self.edit_mode = False
        self._drag_start_pos = None

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(2)
        self.setLayout(self.layout)
        
        # Icon
        self.icon_label = DraggableLabel(name, self)
        self.icon_label.clicked_signal.connect(lambda: self.clicked.emit(self.name))
        self.layout.addWidget(self.icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Name
        self.name_label = QLabel(name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet("font-size: 10px; font-weight: bold; color: white;")
        self.layout.addWidget(self.name_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Location (Found At)
        self.loc_label = QLabel("")
        self.loc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loc_label.setStyleSheet("font-size: 9px; color: #AAAAAA;")
        self.layout.addWidget(self.loc_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.loc_label.hide()
        
    def set_edit_mode(self, enabled):
        self.edit_mode = enabled
        if enabled:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event):
        if self.edit_mode:
            if event.button() == Qt.MouseButton.LeftButton:
                self._drag_start_pos = event.pos()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.edit_mode and self._drag_start_pos:
             # Move Logic
            curr_pos = self.mapToParent(event.pos())
            start_pos_in_parent = self.mapToParent(self._drag_start_pos)
            diff = curr_pos - start_pos_in_parent
            self.move(self.pos() + diff)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.edit_mode:
            self._drag_start_pos = None
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            # Emit change
            if hasattr(self.parent(), '_on_cell_moved'):
                 pass
            # Better: use signal on self
            self.position_changed.emit(self.name, self.x(), self.y())
        else:
            super().mouseReleaseEvent(event)
            
    # Signals
    position_changed = pyqtSignal(str, int, int)
    
    def set_font_size(self, size):
        self.name_label.setStyleSheet(f"font-size: {size}px; font-weight: bold; color: white;")
        self.loc_label.setStyleSheet(f"font-size: {max(8, size-2)}px; color: #AAAAAA;")
        
    def set_pixmap(self, pixmap):
        self.icon_label.setPixmap(pixmap)
        
    def set_location_text(self, text):
        if text:
            self.loc_label.setText(text)
            self.loc_label.show()
        else:
            self.loc_label.hide()


class CharactersCanvas(QWidget):
    """
    Inner canvas that holds the absolute positioned cells.
    """
    def __init__(self, data_loader, state_manager, layout_manager, parent=None):
        super().__init__(parent)
        self.data_loader = data_loader
        self.state_manager = state_manager
        self.layout_manager = layout_manager
        
        self.cells = {} # name -> CharacterCell
        self.edit_mode = False
        
        self.init_ui()
        self.connect_signals()
        
    def init_ui(self):
        # No Layout - Absolute Positioning
        
        # Load Characters
        chars_data = self.data_loader.load_json("characters.json")
        
        excluded = ["Claire", "Lisa", "Marie"]
        heroes = ["Maxim", "Selan", "Guy", "Artea", "Tia", "Dekar", "Lexis"]
        
        items = []
        for h in heroes:
            if h in chars_data:
                items.append(h)
        
        others = [k for k in chars_data.keys() if k not in heroes and k not in excluded]
        items.extend(sorted(others))
        
        # Grid Params
        x = 5
        y = 5
        col = 0
        max_cols = 4 
        spacing_x = 50 
        spacing_y = 60 # Taller for labels
        
        for name in items:
            # Check saved pos
            pos = self.layout_manager.get_position("characters", name)
            
            if pos:
                final_x, final_y = pos
            else:
                final_x = x + (col * spacing_x)
                final_y = y
                
                col += 1
                if col >= max_cols:
                    col = 0
                    y += spacing_y

            cell = CharacterCell(name, self)
            cell.move(final_x, final_y)
            cell.show()
            
            cell.clicked.connect(self.toggle_character)
            cell.position_changed.connect(self._on_cell_moved)
            
            self.cells[name] = cell
            
        self.update_min_size()      
        self.refresh_state()

    def set_edit_mode(self, enabled):
        self.edit_mode = enabled
        for cell in self.cells.values():
            cell.set_edit_mode(enabled)

    def _on_cell_moved(self, name, x, y):
        self.layout_manager.set_position("characters", name, x, y)
        self.update_min_size()

    def update_min_size(self):
        max_x = 0
        max_y = 0
        for cell in self.cells.values():
            max_x = max(max_x, cell.x() + cell.width())
            max_y = max(max_y, cell.y() + cell.height())
        self.setMinimumSize(max_x + 10, max_y + 10)
            
    def connect_signals(self):
        self.state_manager.character_changed.connect(self._on_character_changed)
        self.state_manager.character_assigned.connect(self._on_assignment_changed)
        self.state_manager.character_unassigned.connect(self._on_assignment_changed)

    def _on_character_changed(self, name, obtained):
        self.refresh_state()

    def _on_assignment_changed(self, location, name):
        self.refresh_state()
        
    def set_content_font_size(self, size):
        for cell in self.cells.values():
            cell.set_font_size(size)

    def toggle_character(self, name):
        current = self.state_manager.active_characters.get(name, False)
        self.state_manager.set_character_obtained(name, not current)
        
    def refresh_state(self):
        active_chars = self.state_manager.active_characters
        
        # Get reverse lookup for locations: Character -> Location
        char_locations = {} 
        for loc, char in self.state_manager._character_locations.items():
            char_locations[char] = loc
            
        chars_data = self.data_loader.load_json("characters.json")
        
        for name, cell in self.cells.items():
            if name not in chars_data:
                continue
                
            is_active = active_chars.get(name, False)
            location = char_locations.get(name)
            
            # --- Image Logic ---
            rel_path = chars_data[name]["image_path"]
            full_path = self.data_loader.resolve_image_path(rel_path)
            pix = QPixmap(full_path)
            
            if is_active:
                cell.set_pixmap(pix)
            else:
                # Dimmed / Grayscale
                gray_pix = QPixmap(pix.size())
                gray_pix.fill(Qt.GlobalColor.transparent)
                painter = QPainter(gray_pix)
                painter.setOpacity(0.3) # Dim it
                painter.drawPixmap(0, 0, pix)
                painter.end()
                cell.set_pixmap(gray_pix)
                
            # --- Location Logic ---
            if is_active and location:
                cell.set_location_text(location)
            else:
                cell.set_location_text(None)


class CharactersWidget(QWidget):
    """
    Wrapper widget adding a QScrollArea around the CharactersCanvas.
    Allows the dock to shrink smaller than the content.
    """
    def __init__(self, data_loader, state_manager, layout_manager, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True) # Canvas sets its own MinSize, ScrollArea respects it.
        # Actually setWidgetResizable(True) makes the widget resize to ScrollArea.
        # We want the widget to dictate size if larger, else scroll.
        # But if we setResizable(True), it expands to fill space, but if minSize > area, scrollbars appear.
        
        self.canvas = CharactersCanvas(data_loader, state_manager, layout_manager, self)
        self.scroll_area.setWidget(self.canvas)
        
        self.layout.addWidget(self.scroll_area)
        
    def set_content_font_size(self, size):
        self.canvas.set_content_font_size(size)
        
    def set_edit_mode(self, enabled):
        self.canvas.set_edit_mode(enabled)

    def refresh_state(self):
        # Exposed for external calls if any (MainWindow usually triggers StateManager signals which Canvas listens to?
        # Canvas listens to StateManager signals? No, Canvas init does pass, but doesn't connect signals except 'clicked'.
        # MainWindow call to refresh?
        # CharactersWidget (old) had connect_signals that did 'pass'.
        # But wait, CharactersWidget logic relied on 'self.refresh_state()' being called?
        # It calls it in init_ui. But when does it update?
        # MainWindow used to call it?
        # No, StateManager emits signals. 
        # Ah, in old code:
        # self.cells[name] = cell
        # ...
        # self.refresh_state() 
        # But where is the signal connection?
        # Old code: 'connect_signals' was empty pass.
        # Wait, how did it update on click?
        # toggle_character -> state_manager.set_character_obtained -> emits character_changed.
        # Does CharactersWidget listen to it?
        # Old code: NO! It missed connecting StateManager signals!
        # Except: "We need to refresh when character location assignment changes too... pass"
        # It seems v1.4 CharactersWidget updates might have been broken unless I missed where it connected?
        # Wait, 'toggle_character' updates state manager.
        # We need to listen to 'character_changed' and 'character_assigned'.
        
        self.canvas.refresh_state()
        
    def connect_signals(self):
         # Forward connection? Or better, let Canvas handle it.
         pass
         
    # Better: Connect signals in Canvas

class DraggableLabel(QLabel):
    clicked_signal = pyqtSignal()
    
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.name = name
        self.setFixedSize(40, 40)
        self.setScaledContents(True)

    # Standard click/drag logic handled by parent cell for edit mode?
    # Or keep Assignment Drag separate?
    # Requirement: "Click to assign" vs "Drag to assign" vs "Drag to Move"
    # If Edit Mode is ON:
    #   Left Click -> Select/Move Start
    #   Drag -> Move Widget
    #   Right Click -> Nothing?
    # If Edit Mode is OFF:
    #   Left Click -> Toggle Character
    #   Drag -> Create Drag Object for Map Assignment
    
    # Needs coordination with Parent Cell.
    # Actually the DraggableLabel was doing the heavy lifting for Assignment Drag.
    # We should let the parent handle the "Move Widget" drag.
    
    def mousePressEvent(self, event):
        # We need to know if parent is in edit mode.
        parent = self.parentWidget()
        if parent and hasattr(parent, 'edit_mode') and parent.edit_mode:
            event.ignore() # Let parent handle move drag
        else:
            if event.button() == Qt.MouseButton.LeftButton:
                self.drag_start_position = event.pos()
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        # Assignment Drag (Edit Mode OFF)
        parent = self.parentWidget()
        if parent and hasattr(parent, 'edit_mode') and parent.edit_mode:
            event.ignore()
            return

        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if (event.pos() - self.drag_start_position).manhattanLength() < 10:
            return

        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(self.name)
        drag.setMimeData(mime_data)
        
        pixmap = self.pixmap()
        if pixmap:
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.pos())

        drag.exec(Qt.DropAction.CopyAction | Qt.DropAction.MoveAction)
        
    def mouseReleaseEvent(self, event):
        parent = self.parentWidget()
        if parent and hasattr(parent, 'edit_mode') and parent.edit_mode:
            event.ignore()
            return
            
        self.clicked_signal.emit()
        super().mouseReleaseEvent(event)

class CharacterCell(QWidget):
    """
    Compound widget: Icon + Name Label + Location Label
    """
    clicked = pyqtSignal(str)
    
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.name = name
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0,0,0,0)
    def __init__(self, name, parent=None):
        super().__init__(parent)
        self.name = name
        self.setFixedSize(60, 60) # Increased size for label space
        # self.setScaledContents(True) # Cell is container now
        self.edit_mode = False
        self._drag_start_pos = None

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.setSpacing(2)
        self.setLayout(self.layout)
        
        # Icon
        self.icon_label = DraggableLabel(name, self)
        self.icon_label.clicked_signal.connect(lambda: self.clicked.emit(self.name))
        self.layout.addWidget(self.icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Name
        self.name_label = QLabel(name)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.name_label.setStyleSheet("font-size: 10px; font-weight: bold; color: white;")
        self.layout.addWidget(self.name_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Location (Found At)
        self.loc_label = QLabel("")
        self.loc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loc_label.setStyleSheet("font-size: 9px; color: #AAAAAA;")
        self.layout.addWidget(self.loc_label, alignment=Qt.AlignmentFlag.AlignCenter)
        self.loc_label.hide()
        
    def set_edit_mode(self, enabled):
        self.edit_mode = enabled
        if enabled:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def mousePressEvent(self, event):
        if self.edit_mode:
            if event.button() == Qt.MouseButton.LeftButton:
                self._drag_start_pos = event.pos()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.edit_mode and self._drag_start_pos:
             # Move Logic
            curr_pos = self.mapToParent(event.pos())
            start_pos_in_parent = self.mapToParent(self._drag_start_pos)
            diff = curr_pos - start_pos_in_parent
            self.move(self.pos() + diff)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self.edit_mode:
            self._drag_start_pos = None
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            # Emit change
            if hasattr(self.parent(), '_on_cell_moved'):
                 # Need signals
                 pass
            # Better: use signal on self
            self.position_changed.emit(self.name, self.x(), self.y())
        else:
            super().mouseReleaseEvent(event)
            
    # Signals
    position_changed = pyqtSignal(str, int, int)
    
    def set_font_size(self, size):
        self.name_label.setStyleSheet(f"font-size: {size}px; font-weight: bold; color: white;")
        self.loc_label.setStyleSheet(f"font-size: {max(8, size-2)}px; color: #AAAAAA;")
        
    def set_pixmap(self, pixmap):
        self.icon_label.setPixmap(pixmap)
        
    def set_location_text(self, text):
        if text:
            self.loc_label.setText(text)
            self.loc_label.show()
        else:
            self.loc_label.hide()

class CharactersWidget(QWidget):
    def __init__(self, data_loader, state_manager, layout_manager, parent=None):
        super().__init__(parent)
        self.data_loader = data_loader
        self.state_manager = state_manager
        self.layout_manager = layout_manager
        
        self.cells = {} # name -> CharacterCell
        
        self.init_ui()
        self.connect_signals()
        
    def init_ui(self):
        # No Layout - Absolute Positioning
        
        # Load Characters
        chars_data = self.data_loader.load_json("characters.json")
        
        excluded = ["Claire", "Lisa", "Marie"]
        heroes = ["Maxim", "Selan", "Guy", "Artea", "Tia", "Dekar", "Lexis"]
        
        items = []
        for h in heroes:
            if h in chars_data:
                items.append(h)
        
        others = [k for k in chars_data.keys() if k not in heroes and k not in excluded]
        items.extend(sorted(others))
        
        # Grid Params
        x = 5
        y = 5
        col = 0
        max_cols = 4 
        spacing_x = 50 
        spacing_y = 60 # Taller for labels
        
        for name in items:
            # Check saved pos
            pos = self.layout_manager.get_position("characters", name)
            
            if pos:
                final_x, final_y = pos
            else:
                final_x = x + (col * spacing_x)
                final_y = y
                
                col += 1
                if col >= max_cols:
                    col = 0
                    y += spacing_y

            cell = CharacterCell(name, self)
            cell.move(final_x, final_y)
            cell.show()
            
            cell.clicked.connect(self.toggle_character)
            cell.position_changed.connect(self._on_cell_moved)
            
            self.cells[name] = cell
            
        self.update_min_size()      
        self.refresh_state()

    def set_edit_mode(self, enabled):
        for cell in self.cells.values():
            cell.set_edit_mode(enabled)

    def _on_cell_moved(self, name, x, y):
        self.layout_manager.set_position("characters", name, x, y)
        self.update_min_size()

    def update_min_size(self):
        max_x = 0
        max_y = 0
        for cell in self.cells.values():
            max_x = max(max_x, cell.x() + cell.width())
            max_y = max(max_y, cell.y() + cell.height())
        self.setMinimumSize(max_x + 10, max_y + 10)
            
    def connect_signals(self):
        # We need to refresh when character location assignment changes too
        pass 
        
    def set_content_font_size(self, size):
        for cell in self.cells.values():
            cell.set_font_size(size)

    def toggle_character(self, name):
        current = self.state_manager.active_characters.get(name, False)
        self.state_manager.set_character_obtained(name, not current)
        
    def refresh_state(self):
        active_chars = self.state_manager.active_characters
        
        # Get reverse lookup for locations: Character -> Location
        char_locations = {} 
        for loc, char in self.state_manager._character_locations.items():
            char_locations[char] = loc
            
        chars_data = self.data_loader.load_json("characters.json")
        
        for name, cell in self.cells.items():
            if name not in chars_data:
                continue
                
            is_active = active_chars.get(name, False)
            location = char_locations.get(name)
            
            # --- Image Logic ---
            rel_path = chars_data[name]["image_path"]
            full_path = self.data_loader.resolve_image_path(rel_path)
            pix = QPixmap(full_path)
            
            if is_active:
                cell.set_pixmap(pix)
            else:
                # Dimmed / Grayscale
                gray_pix = QPixmap(pix.size())
                gray_pix.fill(Qt.GlobalColor.transparent)
                painter = QPainter(gray_pix)
                painter.setOpacity(0.3) # Dim it
                painter.drawPixmap(0, 0, pix)
                painter.end()
                cell.set_pixmap(gray_pix)
                
            # --- Location Logic ---
            # User request: "add the location where it was found in Characters to the character"
            if is_active and location:
                cell.set_location_text(location)
            else:
                cell.set_location_text(None)


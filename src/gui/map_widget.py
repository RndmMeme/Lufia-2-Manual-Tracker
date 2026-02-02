from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsEllipseItem, QGraphicsItem, QGraphicsPolygonItem
from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QPixmap, QBrush, QColor, QPainter, QPolygonF, QPen
import logging
from utils.constants import GAME_WORLD_SIZE, CANVAS_SIZE, COLORS

class InteractiveDot(QGraphicsEllipseItem):
    """
    A clickable dot on the map representing a location/city.
    """
    def __init__(self, location_name, x, y, size=10, initial_color="red"):
        # Center the dot on the coordinate
        rect_x = x - (size / 2)
        rect_y = y - (size / 2)
        super().__init__(rect_x, rect_y, size, size)
        
        self.location_name = location_name
        self.setAcceptHoverEvents(True)
        # User feedback: Hand cursor interacts poorly/obscures dots. Using standard Arrow.
        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.setToolTip(location_name)
        
        # Call set_color to apply the brush
        self.set_color(initial_color)

    def set_color(self, color_name):
        qt_color = QColor(COLORS.get(color_name, "red"))
        self.setBrush(QBrush(qt_color))
        self.setPen(QPen(Qt.PenStyle.NoPen))

    def mousePressEvent(self, event):
        """Handle interactions. Left click triggers state toggle via the Scene."""
        # Crucial: Accept event to prevent View from stealing it for Drag/Panning
        event.accept() 
        if event.button() == Qt.MouseButton.LeftButton:
            # Propagate the click to the parent view/scene to handle the logic
            # We can use the scene's method if we define it, or emit a signal from the view
            # For QGraphicsItem, direct signal emission isn't built-in without QObject inheritance.
            # Best practice: The View handles the scene interaction.
             pass
        super().mousePressEvent(event)

class MapWidget(QGraphicsView):
    """
    The main map view.
    Renders map.jpg and overlays interactive dots.
    """
    
    # Signals
    location_clicked = pyqtSignal(str) # name
    location_right_clicked = pyqtSignal(str) # name, for context menu
    
    def __init__(self, data_loader):
        super().__init__()
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        
        # Graphics View Configuration
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Default to Arrow (NoDrag). User must unlock to pan.
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # self.setFixedSize(CANVAS_SIZE[0], CANVAS_SIZE[1]) # Allow resizing
        
        # Scaling Factors
        self._scale_x = CANVAS_SIZE[0] / GAME_WORLD_SIZE[0] # 400 / 4096
        self._scale_y = CANVAS_SIZE[1] / GAME_WORLD_SIZE[1]
        
        # Load Map Image
        map_path = data_loader.resolve_image_path("map/map.jpg")
        self._background_item = QGraphicsPixmapItem(QPixmap(map_path))
        
        # Scale the huge map image down to 400x400 to match the "Canvas Size" logic of V1.3
        # V1.3 did: resized_map_image = map_image.resize((400,400))
        # We can simulate this by transforming the item
        orig_width = self._background_item.pixmap().width()
        orig_height = self._background_item.pixmap().height()
        # Calculate scale to fit 400x400
        bg_scale_x = CANVAS_SIZE[0] / orig_width
        bg_scale_y = CANVAS_SIZE[1] / orig_height
        self._background_item.setTransform(self._background_item.transform().scale(bg_scale_x, bg_scale_y))
        
        self._scene.addItem(self._background_item)
        
        # Store Dot Items
        self._dots = {}
        self._player_arrow = None
        
        # Initialize Locations
        self._init_locations(data_loader.get_locations())
        
        # Initialize Player Arrow
        self._init_player_arrow()

    def _init_locations(self, locations_data):
        """Creates a dot for every location in the JSON."""
        # V1.3 Logic: City Limit = 28 (First 28 are circles, rest are squares?)
        # For V1.4, let's keep it simple with circles first, can add shapes later if strictly needed.
        
        for name, coords in locations_data.items():
            # Apply scaling 4096 -> 400
            canvas_x = coords[0] * self._scale_x
            canvas_y = coords[1] * self._scale_y
            
            dot = InteractiveDot(name, canvas_x, canvas_y)
            self._scene.addItem(dot)
            self._dots[name] = dot

    def _init_player_arrow(self):
        """Creates the inverted triangle for player position."""
        # 10x10 inverted triangle
        # Points relative to (0,0) center
        # Top-Left (-5, -5), Top-Right (5, -5), Bottom (0, 5) -> Inverted means pointing down?
        # V1.3: x1=x, y1=y+height (bottom tip), x2=left, x3=right.
        # So in V1.3 it draws a triangle pointing DOWN to the coordinate.
        
        polygon = QPolygonF([
            QPointF(0, 0),    # Tip at the coordinate
            QPointF(-5, -10), # Top Left
            QPointF(5, -10)   # Top Right
        ])
        
        self._player_arrow = QGraphicsPolygonItem(polygon)
        self._player_arrow.setBrush(QBrush(QColor("orange")))
        self._player_arrow.setPen(QPen(Qt.PenStyle.NoPen))
        self._player_arrow.setZValue(100) # Always on top
        self._scene.addItem(self._player_arrow)
        self._player_arrow.hide() # Hide until first update based heavily on V1.3

    # --- Public Updates ---
    
    def update_dot_color(self, name, color_name):
        if name in self._dots:
            self._dots[name].set_color(color_name)

    def update_dot_tooltip(self, name, text):
        if name in self._dots:
            self._dots[name].setToolTip(text)

    def update_player_position(self, x, y):
        """Updates the arrow position. Checks for out-of-bounds/clipping."""
        # Ensure we don't clip outside (0,0) to (400,400)
        safe_x = max(0, min(x, CANVAS_SIZE[0]))
        safe_y = max(0, min(y, CANVAS_SIZE[1]))
        
        self._player_arrow.setPos(safe_x, safe_y)
        self._player_arrow.setPos(safe_x, safe_y)
        self._player_arrow.show()

    def set_player_arrow_color(self, hex_color: str):
        """Updates the color of the player position arrow."""
        if self._player_arrow:
            self._player_arrow.setBrush(QBrush(QColor(hex_color)))

    # --- Interaction Events ---
    
    def resizeEvent(self, event):
        """Handle resizing to keep the map centered and aspect-ratio correct."""
        if self._scene:
            self.fitInView(self._scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        """Detect clicks on items."""
        item = self.itemAt(event.pos())
        if isinstance(item, InteractiveDot):
            if event.button() == Qt.MouseButton.LeftButton:
                self.location_clicked.emit(item.location_name)
            elif event.button() == Qt.MouseButton.RightButton:
                self.location_right_clicked.emit(item.location_name)
        else:
             # Map Click (Background)
             if event.button() == Qt.MouseButton.RightButton:
                 self._show_context_menu(event.pos())
        
        super().mousePressEvent(event)

    def _show_context_menu(self, pos):
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction
        menu = QMenu(self)
        
        # Rename to "Unlock Map Movement" since default is Locked
        is_locked = (self.dragMode() == QGraphicsView.DragMode.NoDrag)
        unlock_action = QAction("Allow Map Panning (Unlock)", self)
        unlock_action.setCheckable(True)
        unlock_action.setChecked(not is_locked)
        unlock_action.triggered.connect(self._toggle_lock)
        menu.addAction(unlock_action)
        
        menu.exec(self.mapToGlobal(pos))

    def _toggle_lock(self, checked):
        # Checked = Unlocked (Panning allowed)
        if checked:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        else:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)

    # --- Character Sprites ---
    
    def add_character_sprite(self, location, char_name, pixmap_path):
        """Adds a draggable character sprite to the map."""
        if location not in self._dots:
            logging.warning(f"Map: Location {location} not found for char assignment.")
            return

        # Remove existing if any
        self.remove_character_sprite(location)

        # Create Pixmap Item
        pix = QPixmap(pixmap_path)
        # Scale to 30x30 as per v1.3
        pix = pix.scaled(30, 30, Qt.AspectRatioMode.KeepAspectRatio)
        
        item = QGraphicsPixmapItem(pix)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        item.setCursor(Qt.CursorShape.OpenHandCursor)
        
        # Position slightly offset from dot
        dot = self._dots[location]
        dot_x = dot.rect().x()
        dot_y = dot.rect().y()
        item.setPos(dot_x + 10, dot_y - 10)
        
        # Tooltip
        item.setToolTip(f"{char_name} at {location}")
        
        # Text Label removed as per user request

        
        self._scene.addItem(item)
        
        # Store
        if not hasattr(self, '_char_items'):
            self._char_items = {} # loc -> item
        self._char_items[location] = item
        
        # Mark Location as Cleared visually (override)
        # Note: StateManager handles the "Logic" state update which emits location_changed,
        # so MapWidget.update_dot_color handles the dot color.

    def remove_character_sprite(self, location):
        if not hasattr(self, '_char_items'):
            return
            
        item = self._char_items.pop(location, None)
        if item:
            self._scene.removeItem(item)

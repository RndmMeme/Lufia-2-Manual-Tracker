# main.py

import tkinter as tk
import os
import pymem
from pathlib import Path
import logging
import json
from helpers.file_loader import load_image
from helpers.item_management import load_items_and_cache
from gui_setup import setup_interface, setup_canvases
from shared import LOCATIONS, LOCATION_LOGIC, CITIES, tool_items_bw, scenario_items_bw, item_to_location, characters_bw, ALWAYS_ACCESSIBLE_LOCATIONS, load_json_cached, generate_item_to_location_mapping, resolve_relative_path, BASE_DIR, IMAGES_DIR, DATA_DIR, item_spells
from canvas_config import update_character_image, map_address, setup_tools_canvas, setup_scenario_canvas, setup_characters_canvas, setup_maidens_canvas, setup_item_canvas, setup_hints_canvas
from event_handlers import handle_maiden_click, handle_tool_click, handle_scenario_click, handle_dot_click
from logic import LocationLogic
from helpers.resalo import Save, Load, Reset


# Ensure the directory exists
log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)
    
save_dir = "saves"
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

# Configure logging
logging.basicConfig(
    filename=os.path.join(log_dir, 'app.log'),
    filemode='w',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)

# Load item data (**moved to the beginning**)
item_spells = load_items_and_cache()  # This line should be at the beginning

class Lufia2TrackerApp:
    def __init__(self, root):
        
        self.root = root
        self.root.title("Lufia 2 Tracker")

        # Initialize essential attributes
        self.base_dir = BASE_DIR
        self.images_dir = IMAGES_DIR
        self.data_dir = DATA_DIR
        self.script_dir = Path(__file__).parent
        self.entries = {"Shop Item": [], "Spells": [], "Thief": []}
        self.image_cache = {}  # Image cache to avoid repeated loading

        # Initialize essential attributes
        self.map_address = os.path.join(IMAGES_DIR / "map", "map.jpg")
        self.LOCATIONS = LOCATIONS
        
        
        self.game_state = {}
        self.manually_updated_locations = {}
        
        self.location_character_images = {}
        self.item_spells = item_spells
        self.inventory = {}
        self.scenario_items = {}
        self.location_labels = {}
        self.label_visibility = {}
        self.tool_images = {}
        self.scenario_images = {}
        self.maiden_images = {}
        self.character_images = {}
        self.obtained_items = {}
        self.location_states = {location: "not_accessible" for location in LOCATIONS.keys()}
        self.location_labels_visible = True
        self.tool_items_bw = {}
        self.tool_items_c = {}
        self.scenario_items_bw = {}
        self.scenario_items_c = {}
        self.item_to_location = {}
        self.logic = None
        self.update_accessible_locations = True
        self.manual_input_active = False
        self.manually_updated_locations = {}
        self.manual_updates = {}
        self.manual_toggles = {}
        self.image_cache = {}
        self.characters = {}
        self.active_characters = set()  # To keep track of active characters
        self.previous_active_characters = set()
        

        # Image cache to avoid repeated loading
        self.image_cache = {}

        # Load data
        self.load_data()

        # Setup interface
        self.setup_interface()

        # Initialize canvases here
        self.setup_canvases()

        # Setup tools and scenario canvases
        tools_keys = list(tool_items_bw.keys())
        self.tools_canvas, self.tool_images = setup_tools_canvas(root, tools_keys, self.on_tool_click, self.image_cache)
        scenario_keys = list(scenario_items_bw.keys())
        self.scenario_canvas, self.scenario_images = setup_scenario_canvas(root, scenario_keys, item_to_location, self.on_scenario_click, self.image_cache)
        self.characters_canvas, self.character_images = setup_characters_canvas(self.root, self.characters, self.image_cache, self)
        self.maidens_canvas, self.maiden_images = setup_maidens_canvas(root, self.characters, characters_bw, self.image_cache, self, handle_maiden_click)
        

        # Initialize location logic AFTER canvases are set up
        if self.canvas is not None and self.location_labels and self.maidens_images: # Check if all data is available
            self.location_logic = LocationLogic(self.script_dir, self.location_labels, self.canvas, self.maidens_images)
        else:
            if self.characters_canvas is None:
                logging.error("Characters canvas not initialized.")
            if not self.location_labels:
                logging.error("Location labels not initialized.")
            if not self.maidens_images:
                logging.error("Maidens images not initialized.")
            logging.error("Required data (canvas, location_labels, maidens_images) not initialized. Cannot create LocationLogic.")
            # Handle this error appropriately, e.g., exit the application or disable features
            return  # Exit init if data is not available

    def setup_interface(self):
        setup_interface(self)

    def load_data(self):
        try:
            self.locations_logic = load_json_cached(self.data_dir / "locations_logic.json")
            logging.info("Loaded locations logic data.")
        except Exception as e:
            logging.error(f"Failed to load locations logic data: {e}")

        try:
            self.characters = load_json_cached(self.data_dir / "characters.json")
            logging.info("Loaded characters data.")
        except Exception as e:
            logging.error(f"Failed to load characters data: {e}")

        try:
            self.characters_bw = load_json_cached(self.data_dir / "characters_bw.json")
            logging.info("Loaded characters_bw data.")
        except Exception as e:
            logging.error(f"Failed to load characters_bw data: {e}")

        try:
            self.item_to_location = generate_item_to_location_mapping(self.locations_logic)
            logging.info("Generated item to location mapping.")
        except Exception as e:
            logging.error(f"Failed to generate item to location mapping: {e}")

    def setup_canvases(self):
        setup_canvases(self)

    def on_tool_click(self, tool_name):
        handle_tool_click(self, tool_name)

    def on_scenario_click(self, scenario_name):
        handle_scenario_click(self, scenario_name)
        
    def on_maiden_click(self, maiden_name):
        handle_maiden_click(self, maiden_name)   

    def on_dot_click(self, location):
        dot = self.location_labels.get(location)
        if dot:
            current_color = self.canvas.itemcget(dot, "fill")
            next_color = self.get_next_state_color(current_color)
            self.canvas.itemconfig(dot, fill=next_color)
            self.manually_updated_locations[location] = next_color

    def get_next_state_color(self, current_color):
        color_order = ["red", "orange", "lightgreen", "grey"]
        next_index = (color_order.index(current_color) + 1) % len(color_order)
        return color_order[next_index]
    

    def handle_manual_input(self):
        self.manual_input_active = True

        
    def load_image_cached(self, image_path, size=None):
        if image_path not in self.image_cache:
            new_image = load_image(image_path)
            self.image_cache[image_path] = new_image
        return self.image_cache[image_path]
    
    def reset(self):
        self.reset_handler.reset_game_state()

    def save(self):
        self.save_handler.save_game_state()
        
    def load(self):
        self.load_handler.load_game_state()
        

    def on_resize(self, event):
        pass

    def on_closing(self):
        
        self.root.destroy()
 

if __name__ == "__main__":
    root = tk.Tk()
    try:
        app = Lufia2TrackerApp(root)
        root.mainloop()
        app.reset()
        app.load()
        app.save()
    except Exception as e:
        logging.error(f"Unhandled exception: {e}")
        with open("error_log.txt", "a") as error_file:
            error_file.write(f"Unhandled exception: {e}\n")

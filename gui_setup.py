# gui_setup.py

from canvas_config import (
    setup_item_canvas,
    setup_tools_canvas,
    setup_scenario_canvas,
    setup_maidens_canvas,
    setup_characters_canvas,
    setup_hints_canvas,
    setup_canvas,
    update_character_image
)
import tkinter as tk
from tkinter import ttk, filedialog, Label, messagebox
import os
import json
import logging
from PIL import Image, ImageTk
import tkinter.font as tkFont
from shared import characters, characters_bw, CITIES, item_spells, LOCATIONS, COLORS
import pyphen
from helpers.resalo import Reset, Save, Load
from helpers.item_management import create_item_entry, search_item_window 


dic = pyphen.Pyphen(lang='en_US')

# Setting up the general window dimensions
def setup_interface(app):
    """
    Set up the main interface of the application.
    """
    app.root.geometry("700x786")  # Adjusted to a larger view for better visibility
    app.root.bind("<Configure>", app.on_resize)
    app.root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    style = ttk.Style()
    style.configure('Custom.TFrame', background='black')
    style.configure('Custom.TLabel', foreground='white', background='black')
    style.configure('Custom.TButton', width=2)
    
    create_menu(app)
    
    app.root.update()  # Force update

# Setting up the canvases
def setup_canvases(app):
    """
    Set up the various canvases in the application.
    """
    app.canvas, app.map_image, app.map_photo, app.location_labels = setup_canvas(
        app.root, app.map_address, app.LOCATIONS, app.locations_logic, app.inventory, app.scenario_items,
        dot_click_callback=app.on_dot_click, 
        right_click_callback=lambda event, loc: right_click_handler(app, event, loc),
        
    )

    app.item_canvas = setup_item_canvas(app.root)
    
    app.hints_canvas = setup_hints_canvas(app.root)
    
    app.tools_canvas, app.tool_images = setup_tools_canvas(
        app.root, list(app.tool_items_bw.keys()), app.on_tool_click, app.image_cache)    
     
    app.scenario_canvas, app.scenario_images = setup_scenario_canvas(
        app.root, list(app.scenario_items_bw.keys()), app.item_to_location, app.on_scenario_click, app.image_cache)
    
    app.characters_canvas, app.character_images = setup_characters_canvas(app.root, app.characters, app.image_cache, app)
    
    app.maidens_canvas, app.maidens_images = setup_maidens_canvas(app.root, app.characters, app.characters_bw, app.image_cache, app, app.on_maiden_click)

    return app.canvas

# creating and filling the About window
def show_about_window():
    """Show the 'About' window."""
    about_window = tk.Toplevel()
    about_window.title("About")
    about_text = (
        "Thank you for using Lufia 2 Manual Tracker!\n\n"
        "This was my first project and took me quite some time.\n"
        "Feel free to report any bugs or suggestions to\n\n"
        "my git repository:\n"
        "https://github.com/RndmMeme/Lufia-2-Autotracker\n\n"
        "my discord:\n"
        "Rndmmeme#5100\n\n"
        "or the Lufia2 community on discord:\n"
        "Ancient Cave\n\n"
        "Many thanks to\n\n"
        "- abyssonym, the creator of the Lufia2 Randomizer \"terrorwave\"\n"
        "https://github.com/abyssonym/terrorwave\n\n"
        "who patiently explained a lot of the secrets to me :)\n\n"
        "- The3X for testing and feedback\n"
        "https://www.twitch.tv/the3rdx\n\n"
        "- the Lufia2 community\n\n"
        "- and of course you, who decided to use my tracker!\n\n"
        "RndmMeme\n"
        "Lufia 2 Manual Tracker v1.2.1 @2024-2025"
    )
    label = tk.Label(about_window, text=about_text, padx=10, pady=10, justify=tk.LEFT)
    label.pack()
    
    close_button = tk.Button(about_window, text="Close", command=about_window.destroy)
    close_button.pack(pady=10)

# creating and filling the Help window
def show_help_window():
    """Show the 'Help' window."""
    help_window = tk.Toplevel()
    help_window.title("Help")
    help_text = (
        "Welcome to Lufia 2 Manual Tracker!\n\n"
        "If you want to explore the application on your own, feel free to do so.\n"
        "Otherwise here a few tips:\n\n"
        "- Right click on cities (dots) to open the sub menu. Look up your item and\n"
        "  clicking any entry will save it to the items/spells section.\n"
        "- The search window will auto focus. You can also select multiple items. \n"
        "- Double click on an item to save it to the item/spell section.\n"
        "  Press 'ENTER' to add a single or multiple items\n\n"
        "- Right click on locations (squares) to open the character menu. Clicking a character name\n"
        "  will color the character as \"obtained\" and display the location name where you found it\n"
        "- Also a mini sprite of that character will appear on the map at that location\n"
        "- if another location is being obstructed by that image, simply drag and drop it where you like\n\n"
        "- Simply left-clicking any character will color (and discolor) it, too but without location or mini-image.\n\n"
        "- Right click a character you obtained will reset the character and remove the location and mini-image.\n\n"
        "- Left click any square to change the color\n\n"
        "- Colors:\n"
        "red - not accessible\n"
        "orange - partially accessible\n"
        "green - fully accessible\n"
        "grey - cleared\n"
    )
    label = tk.Label(help_window, text=help_text, padx=10, pady=10, justify=tk.LEFT)
    label.pack()

    close_button = tk.Button(help_window, text="Close", command=help_window.destroy)
    close_button.pack(pady=10)

# creating the menu ribbon
def create_menu(app):
    """
    Create the application menu.
    """
    menubar = tk.Menu(app.root)
    app.root.config(menu=menubar)
 
    options_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Options", menu=options_menu)
    
    def reset_game_state():
        Reset(app).reset()
    
    options_menu.add_command(label="Reset", command=reset_game_state)
    
    def save_game_state():
        Save(app).save_game_state() 

    options_menu.add_command(label="Save", command=save_game_state)
    
    def load_game_state():
        Load(app).load_game_state() 

    options_menu.add_command(label="Load", command=load_game_state)

    #options_menu.add_command(label="Location Names", command=app.toggle_location_labels)
    #options_menu.add_command(label="Toggle City Names", command=app.toggle_city_labels)
    
    menubar.add_command(label="About", command=show_about_window)
    menubar.add_command(label="Help", command=show_help_window)

# right click handler for the context menus
def right_click_handler(app, event, location):
    show_context_menu(app, event, location)

def show_context_menu(app, event, location):
    context_menu = tk.Menu(app.root, tearoff=0)

    # Set the font size for the context menu
    new_font = tkFont.Font(family="Helvetica", size=10)  # You can change the size and family as desired
    app.root.option_add("*Menu*Font", new_font)

    if location in CITIES:
        context_menu.add_command(label="Search",
                                 command=lambda: search_item_window(context_menu, location, app))
                                 
    else:
        context_menu.add_command(label="Assign Character", command=lambda: show_character_menu(app, location))

    context_menu.configure(font=new_font)
    context_menu.post(event.x_root, event.y_root)

# functions to add (and remove) location name and mini character image to the map and canvas
     
def update_character_image(canvas, character_images, name, is_active):
    """
    Update the character image to colored if active, or dimmed (black-and-white) if inactive.
    """
    character_info = character_images.get(name)
    if character_info:
        new_image = character_info['color_image'] if is_active else character_info['bw_image']
        canvas.itemconfig(character_info['position'], image=new_image)
        character_info['current_image'] = new_image
        character_info['is_colored'] = is_active
        # Keep a reference to the image to prevent it from being garbage collected
        if not hasattr(canvas, 'images'):
            canvas.images = []
        canvas.images.append(new_image)
        
def make_draggable(canvas, item):
    """Macht ein Canvas-Item mit der Maus verschiebbar."""
    data = {"x": 0, "y": 0}

    def on_drag_start(event):
        """Merkt sich die Startposition der Maus beim Ziehen."""
        data["x"] = event.x
        data["y"] = event.y
        canvas.itemconfig(item, state="normal") #Stellt sicher, dass das Item nicht ausgeblendet ist

    def on_drag_motion(event):
        """Bewegt das Item während des Ziehens."""
        delta_x = event.x - data["x"]
        delta_y = event.y - data["y"]
        canvas.move(item, delta_x, delta_y)
        data["x"] = event.x
        data["y"] = event.y

    def on_drag_release(event):
        """Wird aufgerufen, wenn die Maustaste losgelassen wird."""
        pass # Hier könnten weitere Aktionen ausgeführt werden, z.B. Speichern der neuen Position

    canvas.tag_bind(item, "<ButtonPress-1>", on_drag_start) #ButtonPress anstatt nur Button
    canvas.tag_bind(item, "<B1-Motion>", on_drag_motion)
    canvas.tag_bind(item, "<ButtonRelease-1>", on_drag_release) #ButtonRelease hinzufügen

def show_character_menu(app, location):
    """
    Show character selection menu for assigning a character to the specified location.
    """
    character_menu = tk.Menu(app.root, tearoff=0)

    # Get characters that are not active and not colored
    available_characters = [name for name in app.character_images if name not in app.active_characters and not app.character_images[name]['is_colored']]
    for name in available_characters:
        character_menu.add_command(label=name, command=lambda name=name: assign_character_to_location(app, name, location))
    
    character_menu.post(app.root.winfo_pointerx(), app.root.winfo_pointery())

def assign_character_to_location(app, character_name, location):
    print(f"Assigning character: {character_name} to location: {location}")

    if hasattr(app, 'location_character_images') and location in app.location_character_images:
        existing_character = app.location_character_images[location]['character']
        # *** Remove the existing character ***
        if existing_character:  # Überprüfen, ob ein Charakter existiert, bevor wir ihn entfernen
            remove_character_location(app, existing_character)
            print(f"Removed existing character {existing_character} from {location}")

    image_width = 30
    image_height = 30

    
    update_character_image(app.characters_canvas, app.character_images, character_name, True)

    # Intelligente Textaufteilung (verbessert)
    max_line_length = 9
    words = location.split()
    lines = []
    
    for word in words :
        if len(word) > max_line_length and len(word) > 3:
            hyphenated_word = dic.inserted(word) #Silbentrennung mit pyphen
            parts = hyphenated_word.split("-")
            for part in parts[:-1]: #Alle Teile außer dem letzten
                lines.append(part + "-") #Bindestrich hinzufügen
            lines.append(parts[-1]) #Letzten Teil ohne Bindestrich hinzufügen
        else:
            lines.append(word)

    location_text = "\n".join(lines)
    print(f"Location text: {location_text}")

    char_info = app.character_images.get(character_name)
    if not char_info:
        print(f"Error: No character info found for {character_name}")
        return

    char_image_id = char_info['position']
    char_position = app.characters_canvas.coords(char_image_id)
    print(f"Character position: {char_position}")

    if not char_position:
        print(f"Error: No coordinates found for character image of {character_name}")
        return

    # Text erstellen (mit korrekter Positionierung)
    x_offset = char_position[0] + 1 # Start x-Position des Textes = Start x-Position des Bildes
    y_offset = char_position[1] + image_height + 25 # Direkt unter dem Bild + kleiner Abstand

    text_id = app.characters_canvas.create_text(
        x_offset, y_offset,
        text=location_text,
        fill="white",
        anchor="nw",  # Wichtig: Anker auf "nw" (northwest) setzen
        tags=(f"location_text_{character_name}", "location_text")
    )
    print(f"TextKoords: {x_offset}, {y_offset}")
    app.characters_canvas.tag_bind(char_info['position'], "<Button-3>", lambda event: remove_character_location(app, character_name))

    app.characters_canvas.tag_raise(text_id)
    app.characters_canvas.update_idletasks()

    # *** NEU: Bild auf der Karte hinzufügen ***
    character_image_path = characters[character_name]["image_path"]
    character_image = Image.open(character_image_path)
    
    desired_size =(image_width, image_height)
    character_image_small = character_image.resize(desired_size)  # Größe anpassen

    # Convert to PhotoImage for Tkinter canvas
    character_image_small = ImageTk.PhotoImage(character_image_small)

    # Koordinaten der Location abrufen (jetzt mit location_name)
    location_coords = LOCATIONS[location]
    x_scaled = location_coords[0] * app.canvas.scale_factor_x  # Skalierung in x-Richtung
    y_scaled = location_coords[1] * app.canvas.scale_factor_y  # Skalierung in y-Richtung
    
    # Bild auf der Karte platzieren (mit etwas Offset)
    image_id = app.canvas.create_image(x_scaled + 10, y_scaled - 10, anchor=tk.NW, image=character_image_small, tags=(f"location_image_{character_name}", "location_image"))
    app.canvas.images.append(character_image_small)
    make_draggable(app.canvas, image_id)
    
    # Speichern der Bild-ID und Zuordnung in app
    if not hasattr(app, 'location_character_images'):
        app.location_character_images = {}
    app.location_character_images[location] = {
        'character': character_name, 
        'character_position': char_image_id,
        'canvas_x': x_offset,  # Nur die x-Koordinate
        'canvas_y': y_offset,  # Nur die y-Koordinate
        'image_id': image_id, 
        'coords': (x_scaled + 10, y_scaled - 10), 
        "image_path": characters[character_name]["image_path"]
        } 
    print(f"location_character_images nach Zuweisung: {app.location_character_images}")
   
    # *** NEU: Farbe des Punkts ändern ***
    if location in app.location_labels:  # Überprüfen, ob ein Punkt für die Location existiert
        dot = app.location_labels[location]
        app.canvas.itemconfig(dot, fill=COLORS['cleared']) # Farbe auf "cleared" setzen
    

def remove_character_location(app, character_name):
    print(f"remove_character_location aufgerufen für {character_name}")
    
    text_tags = f"location_text_{character_name}"
    print(f"Versuche, Text mit Tag '{text_tags}' zu löschen")  # Print vor dem Löschen des Textes
    
    app.characters_canvas.delete(text_tags)
    print(f"Text mit Tag '{text_tags}' gelöscht")  # Print nach dem Löschen des Textes

    app.manual_toggles[character_name] = False
    update_character_image(app.characters_canvas, app.character_images, character_name, False)

    # *** NEU: Bild von der Karte entfernen ***
    if hasattr(app, 'location_character_images'):
        locations_to_remove = []
        for location, data in app.location_character_images.items():
            if data['character'] == character_name:
                print(f"Zu löschende image_id (in remove_character_location): {data['image_id']}")  # Überprüfen
                app.canvas.delete(data['image_id'])
                app.canvas.update_idletasks()
                print(f"Mini-image mit ID {data['image_id']} entfernt")
                locations_to_remove.append(location)
        for location in locations_to_remove:
            del app.location_character_images[location]
    print("remove_character_location beendet") # Print am Ende der Funktion

        

    

    

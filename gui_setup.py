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
from shared import characters, characters_bw, CITIES, shop_addresses, item_spells, LOCATIONS
from helpers.memory_utils import read_memory_with_retry



def setup_interface(app):
    """
    Set up the main interface of the application.
    """
    app.root.geometry("870x802")  # Adjusted to a larger view for better visibility
    app.root.bind("<Configure>", app.on_resize)
    app.root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    style = ttk.Style()
    style.configure('Custom.TFrame', background='black')
    style.configure('Custom.TLabel', foreground='white', background='black')
    style.configure('Custom.TButton', width=2)
    
    create_menu(app)
    
    app.root.update()  # Force update
    
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
    app.root.update_idletasks()  # Force update
    
    app.scenario_canvas, app.scenario_images = setup_scenario_canvas(
        app.root, list(app.scenario_items_bw.keys()), app.item_to_location, app.on_scenario_click, app.image_cache)
    app.root.update_idletasks()  # Force update

    app.characters_canvas, app.character_images = setup_characters_canvas(app.root, app.characters, app.image_cache, app)
    
    app.maidens_canvas, app.maidens_images = setup_maidens_canvas(app.root, app.characters, app.characters_bw, app.image_cache, app, app.on_maiden_click)

    return app.canvas

def show_about_window():
    """Show the 'About' window."""
    about_window = tk.Toplevel()
    about_window.title("About")
    about_text = (
        "Thank you for using Lufia 2 Manual Tracker!\n"
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
        "Lufia 2 Manual Tracker v1 @2024"
    )
    label = tk.Label(about_window, text=about_text, padx=10, pady=10, justify=tk.LEFT)
    label.pack()
    
    close_button = tk.Button(about_window, text="Close", command=about_window.destroy)
    close_button.pack(pady=10)

def show_help_window():
    """Show the 'Help' window."""
    help_window = tk.Toplevel()
    help_window.title("Help")
    help_text = (
        "Welcome to Lufia 2 Manual Tracker!\n"
        "If you want to explore the application on your own, feel free to do so.\n"
        "Otherwise here a few tips:\n\n"
        "- Right click on cities (pink dots) to open the sub menu. Look up your item and clicking any entry will save it to the items/spells canvas.\n"
        "- Right click on locations (other color) to open character menu. Clicking a character name will color the character \n"
        "  as \"obtained\" and display the location name where you found it\n"
        "- Simply left-clicking any character will color it, too.\n"
        "- Right click a character you obtained will reset the character and remove the location\n"
        "- Left click any location dot will change the color\n"
        "Colors: red - not accessible\n"
        "        orange - partially accessible\n"
        "        green - fully accessible\n"
        "        grey - cleared\n"
    )
    label = tk.Label(help_window, text=help_text, padx=10, pady=10, justify=tk.LEFT)
    label.pack()

    close_button = tk.Button(help_window, text="Close", command=help_window.destroy)
    close_button.pack(pady=10)

def create_menu(app):
    """
    Create the application menu.
    """
    menubar = tk.Menu(app.root)
    app.root.config(menu=menubar)
 
    options_menu = tk.Menu(menubar, tearoff=0)
    #menubar.add_cascade(label="Options", menu=options_menu)
 
    def save_game_state_wrapper():  # Define the function directly
        save_game_state(app)

    # options_menu.add_command(label="Save", command=save_game_state_wrapper)

    def load_game_state_wrapper():  # Define the function directly
        load_game_state(app)

    # options_menu.add_command(label="Load", command=load_game_state_wrapper)

    #options_menu.add_command(label="Location Names", command=app.toggle_location_labels)
    #options_menu.add_command(label="Toggle City Names", command=app.toggle_city_labels)
    
    menubar.add_command(label="About", command=show_about_window)
    menubar.add_command(label="Help", command=show_help_window)

def right_click_handler(app, event, location):
    show_context_menu(app, event, location)

def show_context_menu(app, event, location):
    context_menu = tk.Menu(app.root, tearoff=0)
    
    # Set the font size for the context menu
    new_font = tkFont.Font(family="Helvetica", size=10)  # You can change the size and family as desired
    app.root.option_add("*Menu*Font", new_font)
    
    if location in CITIES:
        weapon_menu = tk.Menu(context_menu, tearoff=0, font=new_font)
        weapon_menu.add_command(label="Search Weapon", command=lambda: search_item_window(context_menu, "Weapon", app.item_spells["Weapon"], location, app))
        context_menu.add_cascade(label="Weapon", menu=weapon_menu)

        armor_menu = tk.Menu(context_menu, tearoff=0, font=new_font)
        armor_menu.add_command(label="Search Armor", command=lambda: search_item_window(context_menu, "Armor", app.item_spells["Armor"], location, app))
        context_menu.add_cascade(label="Armor", menu=armor_menu)

        spell_menu = tk.Menu(context_menu, tearoff=0, font=new_font)
        spell_menu.add_command(label="Search Spell", command=lambda: search_item_window(context_menu, "Spell", app.item_spells["Spell"], location, app))
        context_menu.add_cascade(label="Spell", menu=spell_menu)
    else:
        context_menu.add_command(label="Assign Character", command=lambda: show_character_menu(app, location))

    context_menu.configure(font=new_font)
    context_menu.post(event.x_root, event.y_root)



def store_shop_item(app, location, item_name, hex_value, category):
    canvas = app.item_canvas if category in ["weapon", "armor", "iris treasures", "spell"] else None
    if canvas:
        bbox = canvas.bbox("all")
        y = bbox[3] + 20 if bbox else 30

        text_id = canvas.create_text(10, y, anchor='nw', text=f"{location}: {item_name} ({hex_value})", fill="white", font=('Arial', 10))
        button_id = canvas.create_text(260, y, anchor='nw', text="x", fill="red", font=('Arial', 10, 'bold'))

        canvas.tag_bind(button_id, "<Button-1>", lambda event, tid=text_id, bid=button_id: remove_entry(canvas, tid, bid))
        canvas.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))
        canvas.yview_moveto(1.0)

def remove_entry(canvas, text_id, button_id):
    canvas.delete(text_id)
    canvas.delete(button_id)
    canvas.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

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

    app.manual_toggles[character_name] = True
    update_character_image(app.characters_canvas, app.character_images, character_name, True)

    # Intelligente Textaufteilung (wie zuvor)
    max_line_length = 12
    words = location.split()
    lines = []
    current_line = ""
    for word in words:
        if len(current_line) + len(word) + 1 <= max_line_length:
            current_line += word + " "
        else:
            lines.append(current_line.strip())
            current_line = word + " "
    lines.append(current_line.strip())
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

    # Text erstellen (zuerst an temporärer Position)
    text_id = app.characters_canvas.create_text(
        0, 0,  # Temporäre Koordinaten
        text=location_text,
        fill="white",
        anchor="nw",
        tags=(f"location_text_{character_name}", "location_text")
    )

    # Textbreite ermitteln
    bbox = app.characters_canvas.bbox(text_id)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # *** Verbesserte Textpositionierung ***
    x_offset = char_position[0]  # Start x-Position des Textes = Start x-Position des Bildes
    y_offset = char_position[1] + 60 #Direkt unter dem Namen

    # Text zentrieren (horizontal)
    x_offset += 45 - (text_width // 2) #20 ist der Offset im Canvas_Config

    app.characters_canvas.coords(text_id, x_offset, y_offset)
    app.characters_canvas.itemconfig(text_id, anchor="n")

    app.characters_canvas.tag_bind(char_info['position'], "<Button-3>", lambda event: remove_character_location(app, character_name))

    app.characters_canvas.tag_raise(text_id)
    app.characters_canvas.update_idletasks()

    # *** NEU: Bild auf der Karte hinzufügen ***
    character_image_path = characters[character_name]["image_path"]
    character_image = Image.open(character_image_path)
    
    desired_size =(30, 30)
    character_image_small = character_image.resize(desired_size)  # Größe anpassen

    # Convert to PhotoImage for Tkinter canvas
    character_image_small = ImageTk.PhotoImage(character_image_small)

    # Koordinaten der Location abrufen (jetzt mit location_name)
    location_coords = LOCATIONS[location]
    x_scaled = location_coords[0] * app.canvas.scale_factor_x  # Skalierung in x-Richtung
    y_scaled = location_coords[1] * app.canvas.scale_factor_y  # Skalierung in y-Richtung

    # Bild auf der Karte platzieren (mit etwas Offset)
    image_id = app.canvas.create_image(x_scaled + 10, y_scaled - 10, anchor=tk.NW, image=character_image_small)
    app.canvas.images.append(character_image_small)

    # Speichern der Bild-ID und Zuordnung in app
    if not hasattr(app, 'location_character_images'):
        app.location_character_images = {}
    app.location_character_images[location] = {'character': character_name, 'image_id': image_id}

    

def remove_character_location(app, character_name):
    text_tags = f"location_text_{character_name}"
    app.characters_canvas.delete(text_tags)
    app.manual_toggles[character_name] = False
    update_character_image(app.characters_canvas, app.character_images, character_name, False)

    # *** NEU: Bild von der Karte entfernen ***
    if hasattr(app, 'location_character_images'):
        locations_to_remove = []
        for location, data in app.location_character_images.items():
            if data['character'] == character_name:
                app.canvas.delete(data['image_id'])
                locations_to_remove.append(location)
        for location in locations_to_remove:
            del app.location_character_images[location]

def load_items_and_cache():
    """Loads items/spells from the JSON file and caches them for faster lookup."""
    try:
        # Konvertiere das Dictionary in eine Liste von Dictionaries
        processed_items = {}
        for category, items in item_spells.items():
            processed_items[category] = [{"name": name} for name in items.values()] # Nur die Namen
        return processed_items
    except Exception as e: # Fange alle Exceptions
        print(f"Error loading items: {e}")
        return {}
    
def search_item_window(parent, category, items, location, app): # location und app hinzugefügt
    """Opens a search window for items/spells."""
    search_window = tk.Toplevel(parent)
    search_window.title(f"Search {category}")

    entry_field = ttk.Entry(search_window, width=30)
    entry_field.pack()

    suggestions_listbox = tk.Listbox(search_window)
    suggestions_listbox.pack()

    def update_suggestions(event=None):
        input_text = entry_field.get().lower()
        suggestions_listbox.delete(0, tk.END)
        for item in app.item_spells[category]:
            # Check if the input text is contained within the item name (case-insensitive)
            if input_text in item['name'].lower(): 
                suggestions_listbox.insert(tk.END, item['name'])

    entry_field.bind("<KeyRelease>", update_suggestions)
    #Damit die Liste direkt beim Öffnen des Fensters gefüllt wird
    update_suggestions()

    def item_selected(event):
        try:
            selected_item_name = suggestions_listbox.get(suggestions_listbox.curselection())
            store_shop_item(app, location, selected_item_name, selected_item_name, category.lower())  # Use name directly
            search_window.destroy()
        except IndexError:
            pass

    suggestions_listbox.bind("<Double-Button-1>", item_selected)
    

import sys
import os
from PyQt6.QtCore import QObject

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from core.data_loader import DataLoader
from core.logic_engine import LogicEngine
from core.state_manager import StateManager

class SignalCatcher(QObject):
    def __init__(self):
        super().__init__()
        self.events = []
    
    def on_location_changed(self, name, state):
        self.events.append(f"Location {name} -> {state}")

    def on_char_assigned(self, location, name):
        self.events.append(f"Assigned {name} at {location}")

def verify_phase2():
    print("--- Verifying Phase 2 Logic ---")
    data_loader = DataLoader() # Loads JSONs
    logic_engine = LogicEngine(data_loader)
    state_manager = StateManager(logic_engine)
    
    catcher = SignalCatcher()
    state_manager.location_changed.connect(catcher.on_location_changed)
    state_manager.character_assigned.connect(catcher.on_char_assigned)
    
    # 1. Verify Daos' Shrine Logic
    # Access Rules: ["Claire,Lisa,Marie, Engine"]
    print("\n[Test 1] Daos' Shrine Accessibility")
    
    daos_key = "Daos' Shrine"
    
    # Initial State (Empty Inventory)
    access = logic_engine.calculate_accessibility(state_manager.inventory)
    print(f"Initial: {access.get(daos_key, False)} (Expected False)")
    
    # Add Engine only
    state_manager.toggle_manual_inventory("Engine")
    access = logic_engine.calculate_accessibility(state_manager.inventory)
    print(f"With Engine: {access.get(daos_key, False)} (Expected False)")
    
    # Add Maidens
    state_manager.toggle_manual_inventory("Claire")
    state_manager.toggle_manual_inventory("Lisa")
    state_manager.toggle_manual_inventory("Marie")
    
    access = logic_engine.calculate_accessibility(state_manager.inventory)
    print(f"With Engine + 3 Maidens: {access.get(daos_key, False)} (Expected True)")
    
    # 2. Verify Character Assignment
    print("\n[Test 2] Character Assignment")
    loc = "Alunze"
    char = "Guy"
    
    state_manager.assign_character_to_location(loc, char)
    
    # Check state
    print(f"Character at {loc}: {state_manager.get_character_at_location(loc)} (Expected {char})")
    print(f"Active Characters: {state_manager.active_characters.get(char)} (Expected True)")
    
    # 3. Verify Reassignment (Move)
    print("\n[Test 3] Character Reassignment (Move)")
    loc2 = "Tanbel"
    
    # Move Guy from Alunze to Tanbel
    state_manager.assign_character_to_location(loc2, char)
    
    print(f"Character at {loc} (Old): {state_manager.get_character_at_location(loc)} (Expected None)")
    print(f"Character at {loc2} (New): {state_manager.get_character_at_location(loc2)} (Expected {char})")
    print(f"Active Characters: {state_manager.active_characters.get(char)} (Expected True)")
    
    # 4. Verify Overwrite (Displace)
    print("\n[Test 4] Character Overwrite")
    char2 = "Dekar"
    
    # Assign Dekar to Tanbel (Where Guy is)
    state_manager.assign_character_to_location(loc2, char2)
    
    print(f"Character at {loc2}: {state_manager.get_character_at_location(loc2)} (Expected {char2})")
    print(f"Active Characters ({char2}): {state_manager.active_characters.get(char2)} (Expected True)")
    print(f"Active Characters ({char}): {state_manager.active_characters.get(char)} (Expected False/Dimmed)")
    
    # Check signals
    print("\nSignals Received:")
    for e in catcher.events:
        print(f"  - {e}")

if __name__ == "__main__":
    verify_phase2()

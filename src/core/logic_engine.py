import logging
from typing import Dict, Set, Any
from core.data_loader import DataLoader
from utils.constants import ALWAYS_ACCESSIBLE_LOCATIONS

class LogicEngine:
    """
    Pure logic component that determines location accessibility.
    Decoupled from UI and State. 
    Accepts inventory/state snapshots and returns accessibility maps.
    """
    
    def __init__(self, data_loader: DataLoader):
        self._locations_logic = data_loader.get_locations_logic()
        self._cities = data_loader.get_cities()
        
    def calculate_accessibility(self, inventory: Dict[str, bool]) -> Dict[str, bool]:
        """
        Calculates accessibility for ALL locations based on current inventory.
        Input: inventory dict {item_name: bool}
        Output: accessibility dict {location_name: bool}
        """
        # Convert inventory dict to a set of obtained items for faster lookup
        obtained_items_set = {item for item, obtained in inventory.items() if obtained}
        
        accessibility_map = {}
        # Iterate over both Logic locations AND Cities (which might be missing from logic)
        all_relevant_locations = set(self._locations_logic.keys()) | set(self._cities.keys())
        
        for location in all_relevant_locations:
            is_accessible = self._check_location(location, obtained_items_set)
            accessibility_map[location] = is_accessible
            
        return accessibility_map

    def get_missing_requirements(self, location, inventory):
        """
        Returns a list of missing items/conditions for a specific location.
        """
        logic = self._locations_logic.get(location)
        if not logic:
            return []
            
        access_rules = logic.get("access_rules", [])
        if not access_rules:
            return []
            
        # Helper to format a single rule
        formatted_rules = []
        for rule in access_rules:
            # Rule is typically a list of requirements (AND) or a single string
            if isinstance(rule, list):
                 # e.g. ["Bomb", "Hook"] -> "Bomb & Hook"
                 # Filter out empty strings or None
                 reqs = [str(r) for r in rule if r]
                 formatted_rules.append(" & ".join(reqs))
            elif isinstance(rule, str):
                 formatted_rules.append(rule)
            else:
                 formatted_rules.append(str(rule))
                 
        # Deduplicate
        formatted_rules = sorted(list(set(formatted_rules)))
        
        # If no rules, return empty
        if not formatted_rules:
            return []
            
        return formatted_rules

    def _check_location(self, location: str, obtained_items: Set[str]) -> bool:
        """
        Determines if a single location is accessible.
        Logic ported directly from v1.3 LocationLogic.is_location_accessible
        """
        # 1. Always Accessible Check
        if location in ALWAYS_ACCESSIBLE_LOCATIONS:
            return True
            
        logic = self._locations_logic.get(location)
        if logic is None:
            # If it's a City with no logic defined, it's considered accessible (Yellow) by default in v1.3
            if location in self._cities:
                return True
            return False # Not in logic file and not a city? Default to inaccessible.

        access_rules = logic.get("access_rules", [])
        
        # 2. Empty rules = Accessible
        if not access_rules:
            return True 
            
        # 3. Rule Evaluation (OR Logic between list items)
        for rule in access_rules:
            # Rule is a string like "Bomb,Hook" (AND Logic)
            required_items = [item.strip() for item in rule.split(',')]
            
            # Check if ALL required items for this rule are present
            if all(req in obtained_items for req in required_items):
                return True
                
        # If no rule is satisfied
        return False

    def determine_color(self, location: str, is_accessible: bool, is_cleared: bool) -> str:
        """
        Determines the semantic color/state for the UI.
        Prioritizes: Cleared > Manual Override (handled by StateManager) > Logic
        """
        if is_cleared:
            return "cleared"
            
        if location in ALWAYS_ACCESSIBLE_LOCATIONS:
            return "accessible"
            
        if location in self._cities:
            # Cities are Yellow ('city') if accessible, Red ('not_accessible') if not.
            # Some users prefer cities always Yellow? v1.3 says Red if requirements missing.
            return "city" if is_accessible else "not_accessible"
            
        return "fully_accessible" if is_accessible else "not_accessible"

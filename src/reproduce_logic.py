from core.data_loader import DataLoader
from core.logic_engine import LogicEngine
from utils.constants import ALWAYS_ACCESSIBLE_LOCATIONS

def test_logic():
    print("--- Starting Logic Debug ---")
    dl = DataLoader()
    le = LogicEngine(dl)
    
    print(f"Always Accessible: {ALWAYS_ACCESSIBLE_LOCATIONS}")
    
    # Test 1: Always Accessible Location
    target = "Foomy Woods"
    # Create a dummy inventory
    inv = {} 
    
    access = le.calculate_accessibility(inv)
    is_acc = access.get(target)
    print(f"Checking {target} (Empty Inv): {is_acc}")
    
    if is_acc:
        print("PASS: Foomy Woods is accessible.")
    else:
        print("FAIL: Foomy Woods is NOT accessible.")
        
    # Test 2: Logic Check
    # Alunze Caves requires Bomb and Hammer
    target_cave = "Alunze Cave"
    print(f"Checking {target_cave} (Empty Inv): {access.get(target_cave)}")
    
    inv_full = {"Bomb": True, "Hammer": True}
    access_full = le.calculate_accessibility(inv_full)
    is_acc_full = access_full.get(target_cave)
    print(f"Checking {target_cave} (Bomb+Hammer): {is_acc_full}")
    
    if is_acc_full:
        print("PASS: Alunze Cave is accessible with items.")
    else:
        print("FAIL: Alunze Cave is NOT accessible with items.")
        
    print("--- End Logic Debug ---")

if __name__ == "__main__":
    test_logic()

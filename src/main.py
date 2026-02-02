import sys
import logging
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow
from core.data_loader import DataLoader
from core.logic_engine import LogicEngine
from core.state_manager import StateManager
from network.data_listener import DataListener

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Lufia 2 Auto Tracker")
    
    # Core Components
    # root_dir is handled internally by utils.constants
    data_loader = DataLoader()
    logic_engine = LogicEngine(data_loader)
    state_manager = StateManager(logic_engine)
    
    # Network Listener
    data_listener = DataListener(port=65432)
    data_listener.data_received.connect(state_manager.process_auto_update)

    # GUI
    window = MainWindow(state_manager, data_loader, logic_engine, data_listener)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

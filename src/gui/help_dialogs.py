from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

class BaseInfoDialog(QDialog):
    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(400, 500)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Text Area
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setHtml(content)
        layout.addWidget(self.text_edit)
        
        # Close Button
        btn = QPushButton("Close")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

class AboutDialog(BaseInfoDialog):
    def __init__(self, parent=None):
        content = """
        <h3>Lufia 2 Auto Tracker v1.4</h3>
        <p><b>My Discord:</b><br>Rndmmeme#5100</p>
        
        <p><b>Lufia 2 Community on Discord:</b><br>Ancient Cave</p>
        
        <p><b>Many thanks to:</b></p>
        <ul>
            <li><b>abyssonym</b> (Creator of Lufia 2 Randomizer "terrorwave"):<br>
            <a href="https://github.com/abyssonym/terrorwave">https://github.com/abyssonym/terrorwave</a><br>
            who patiently explained a lot of the secrets to me :)</li>
            
            <li><b>The3X</b> (Testing and Feedback):<br>
            <a href="https://www.twitch.tv/the3rdx">https://www.twitch.tv/the3rdx</a></li>
            
            <li>The Lufia 2 Community</li>
            
            <li>And of course, you, who decided to use my tracker!</li>
        </ul>
        
        <p><b>Disclaimer:</b><br>
        If you want to use this tracker for competitive plays please make sure it is accepted for tracking. 
        Also make sure to either not use the auto tracking function or to ask whether it is allowed to be used.</p>
        
        <p><b>RndmMeme</b><br>
        Lufia 2 Auto Tracker v1.3 @2024-2025<br>
        Ported to v1.4 (PyQt6) @2026</p>
        """
        super().__init__("About", content, parent)

class HelpDialog(BaseInfoDialog):
    def __init__(self, parent=None):
        content = """
        <h3>Welcome to Lufia 2 Auto Tracker!</h3>
        <p>If you want to explore the application on your own, feel free to do so. Otherwise, here are a few tips:</p>
        
        <h4>UI Features:</h4>
        <ul>
            <li><b>Docks:</b> Panels can be dragged, floated (popped out), or rearranged freely.</li>
            <li><b>Font Size:</b> Enable 'Font Size Adj' in Options to show (+/-) buttons on each dock title.</li>
            <li><b>Header Color:</b> Pick your color to fit your style.</li>
            <li><b>Free Placement:</b> Toggle 'Edit Layout' in Options to enable drag-and-drop for all items in Characters, Maidens, Tools, and Keys widgets. Your custom layout is saved automatically.</li>
        </ul>

        <h4>Item/Spell Management:</h4>
        <ul>
            <li><b>Right-click on cities (dots)</b> to open the sub-menu.</li>
            <li>Search for your item and click on an entry to save it.</li>
            <li>Double-click on an item to save it. Press 'ENTER' to add one or more items.</li>
        </ul>
        
        <h4>Character Management:</h4>
        <ul>
            <li><b>Right-click on locations</b> to open the character menu.</li>
            <li>Click on a character name to mark as 'obtained'. A mini sprite will appear.</li>
            <li>Drag and drop the sprite if it obscures something.</li>
            <li>Left-click on a character to color/uncolor it without location.</li>
            <li>Right-click on an obtained character to reset it.</li>
        </ul>
        
        <h4>Location Management:</h4>
        <ul>
            <li><b>Left-click on a dot</b> to change its color.</li>
        </ul>
        
        <h4>Color Codes:</h4>
        <ul>
            <li><span style="color:red">Red</span>: Not accessible</li>
            <li><span style="color:orange">Orange</span>: Partially accessible</li>
            <li><span style="color:green">Green</span>: Fully accessible</li>
            <li><span style="color:grey">Grey</span>: Cleared</li>
            <li><span style="color:#CCCC00">Yellow</span>: City (Standard)</li>
        </ul>
        
        <h4>Tracker:</h4>
        <ul>
            <li>Pressing any subcategory in 'Sync' will read your ingame progress (One-Shot).</li>
            <li>'Auto' toggles continuous tracking.</li>
            <li>'Player Color' lets you choose the color of the dot for your player position.</li>
        </ul>
        
        """
        super().__init__("Help", content, parent)

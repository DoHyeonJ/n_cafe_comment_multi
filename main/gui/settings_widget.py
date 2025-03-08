from PyQt5.QtWidgets import (QWidget, QPushButton, QVBoxLayout, 
                           QHBoxLayout, QGroupBox)
from ..utils.log import Log

class SettingsWidget(QWidget):
    def __init__(self, log: Log):
        super().__init__()
        self.log = log
        self.init_ui()

    def init_ui(self):
        group_box = QGroupBox()
        layout = QHBoxLayout()

        self.save_btn = QPushButton('설정 저장')
        self.load_btn = QPushButton('설정 불러오기')
        self.init_btn = QPushButton('설정 초기화')

        layout.addWidget(self.save_btn)
        layout.addWidget(self.load_btn)
        layout.addWidget(self.init_btn)
        
        group_box.setLayout(layout)
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(group_box)
        self.setLayout(main_layout) 
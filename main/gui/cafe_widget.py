from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QComboBox, QCheckBox, QGroupBox,
                           QSpinBox, QPushButton, QMessageBox, QDialog, QListWidget)
from ..utils.log import Log
from .styles import DARK_STYLE
from ..api.cafe import CafeAPI

class CafeWidget(QWidget):
    def __init__(self, log):
        super().__init__()
        self.log = log
        self.cafe_list = []
        self.headers = None
        self.current_boards = []
        self.current_headers = None
        self.current_cafe_id = None 
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 카페 선택
        cafe_label = QLabel("카페 선택")
        cafe_label.setStyleSheet("color: white; font-weight: bold;")
        
        self.cafe_combo = QComboBox()
        self.cafe_combo.setMinimumWidth(250)  # 너비 축소
        self.cafe_combo.currentIndexChanged.connect(self.on_cafe_selected)
        
        # 게시판 선택
        board_label = QLabel("게시판 선택")
        board_label.setStyleSheet("color: white; font-weight: bold;")
        
        self.board_combo = QComboBox()
        self.board_combo.setMinimumWidth(250)  # 너비 축소
        
        # 레이아웃 구성
        layout.addWidget(cafe_label)
        layout.addWidget(self.cafe_combo)
        layout.addWidget(board_label)
        layout.addWidget(self.board_combo)
        layout.addStretch()
        
        self.setLayout(layout)
        
    def update_cafe_list(self, cafe_list, headers):
        """카페 목록 업데이트"""
        self.cafe_list = cafe_list
        self.headers = headers
        
        # 카페 콤보박스 초기화
        self.cafe_combo.clear()
        
        # 카페 목록 추가
        if cafe_list:
            # 데이터 형식 확인
            if isinstance(cafe_list[0], tuple):
                # 튜플 형식 (cafe_id, cafe_url, cafe_name)
                for cafe_id, cafe_url, cafe_name in cafe_list:
                    self.cafe_combo.addItem(cafe_name, cafe_id)
                    # 내부 저장용 리스트 형식 변환
                    if not isinstance(self.cafe_list[0], dict):
                        self.cafe_list = [
                            {'cafe_id': cid, 'cafe_url': curl, 'cafe_name': cname}
                            for cid, curl, cname in cafe_list
                        ]
            else:
                # 딕셔너리 형식
                for cafe in cafe_list:
                    self.cafe_combo.addItem(cafe['cafe_name'], cafe['cafe_id'])
            
        # 첫 번째 카페 선택 (있는 경우)
        if self.cafe_combo.count() > 0:
            self.cafe_combo.setCurrentIndex(0)
            self.on_cafe_selected(0)
    
    def on_cafe_selected(self, index):
        """카페 선택 시 게시판 목록 업데이트"""
        if index < 0 or not self.headers:
            return
            
        cafe_id = self.cafe_combo.currentData()
        if not cafe_id:
            return
            
        self.current_cafe_id = cafe_id
        
        # 게시판 목록 가져오기
        cafe_api = CafeAPI(self.headers)
        board_list = cafe_api.get_board_list(cafe_id)
        
        # 게시판 목록 업데이트
        self.board_combo.clear()
        self.current_boards = board_list
        
        if board_list:
            for board in board_list:
                self.board_combo.addItem(board['board_name'], board['board_id'])
    
    def get_selected_cafe(self):
        """선택된 카페 정보 반환"""
        if self.cafe_combo.count() == 0:
            return None
            
        cafe_id = self.cafe_combo.currentData()
        cafe_name = self.cafe_combo.currentText()
        
        for cafe in self.cafe_list:
            if cafe['cafe_id'] == cafe_id:
                return cafe
                
        return None
    
    def get_selected_board(self):
        """선택된 게시판 정보 반환"""
        if self.board_combo.count() == 0:
            return None
            
        board_id = self.board_combo.currentData()
        board_name = self.board_combo.currentText()
        
        if not self.current_boards:
            return None
            
        for board in self.current_boards:
            if board['board_id'] == board_id:
                return board
                
        return None
    
    def get_settings(self):
        """카페 설정 정보 반환"""
        selected_cafe = self.get_selected_cafe()
        selected_board = self.get_selected_board()
        
        if not selected_cafe or not selected_board:
            return {}
            
        return {
            'cafe_id': selected_cafe['cafe_id'],
            'cafe_name': selected_cafe['cafe_name'],
            'cafe_url': selected_cafe['cafe_url'],
            'board_id': selected_board['board_id'],
            'board_name': selected_board['board_name']
        }
    
    def load_settings(self, settings):
        """설정값 로드"""
        # 카페 설정
        cafe_name = settings.get('cafe_name', '')
        index = self.cafe_combo.findText(cafe_name)
        if index >= 0:
            self.cafe_combo.setCurrentIndex(index)
        
        # 게시판 설정
        board_name = settings.get('board_name', '')
        index = self.board_combo.findText(board_name)
        if index >= 0:
            self.board_combo.setCurrentIndex(index)
    
    def clear_settings(self):
        """설정 초기화"""
        self.cafe_combo.clear()
        self.board_combo.clear()
        self.cafe_list = []
        self.headers = None
        self.current_boards = []
        self.current_headers = None
        self.current_cafe_id = None 
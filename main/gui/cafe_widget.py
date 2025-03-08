from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QComboBox, QCheckBox, QGroupBox,
                           QSpinBox, QPushButton, QMessageBox, QDialog, QListWidget)
from ..utils.log import Log
from .styles import DARK_STYLE
from ..api.cafe import CafeAPI
import os
from ..utils.nickname_generator import generate_nicknames

class NicknameDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("닉네임 목록")
        self.setMinimumSize(400, 500)
        self.init_ui()
        self.load_nicknames()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 닉네임 개수 표시 레이블
        self.count_label = QLabel("닉네임 수: 0개")
        layout.addWidget(self.count_label)
        
        # 닉네임 목록
        self.nickname_list = QListWidget()
        layout.addWidget(self.nickname_list)
        
        # 버튼 레이아웃
        btn_layout = QHBoxLayout()
        
        # 닉네임 랜덤 생성 버튼
        self.generate_btn = QPushButton("닉네임 랜덤 생성")
        self.generate_btn.clicked.connect(self.generate_random_nicknames)
        
        # 닫기 버튼
        self.close_btn = QPushButton("닫기")
        self.close_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.generate_btn)
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def load_nicknames(self):
        self.nickname_list.clear()
        
        if os.path.exists('nickname.txt'):
            with open('nickname.txt', 'r', encoding='utf-8') as f:
                nicknames = f.read().splitlines()
                
            for nickname in nicknames:
                if nickname.strip():  # 빈 줄 제외
                    self.nickname_list.addItem(nickname)
            
            self.count_label.setText(f"닉네임 수: {self.nickname_list.count()}개")
        else:
            self.count_label.setText("닉네임 파일이 없습니다.")
    
    def generate_random_nicknames(self):
        reply = QMessageBox.question(
            self, '닉네임 생성',
            '새로운 닉네임 1000개를 생성하시겠습니까?\n기존 닉네임은 덮어씌워집니다.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            generate_nicknames()
            self.load_nicknames()
            QMessageBox.information(self, '완료', '1000개의 닉네임이 생성되었습니다.')

class CafeWidget(QWidget):
    def __init__(self, log):
        super().__init__()
        self.log = log
        self.current_cafe_id = None
        self.current_headers = None  # 현재 선택된 계정의 헤더 저장
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 카페 선택 영역
        cafe_group = QGroupBox("카페 목록")
        cafe_group.setStyleSheet("""
            QGroupBox {
                color: white;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                margin-top: 8px;
                padding: 12px;
                font-size: 12px;
            }
            QComboBox {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
                min-height: 30px;
                font-size: 12px;
            }
            QComboBox:hover {
                border: 1px solid #5c85d6;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
            QLabel {
                color: white;
                font-size: 12px;
            }
        """)

        cafe_layout = QVBoxLayout()
        cafe_layout.setSpacing(8)

        # 카페 선택
        cafe_label = QLabel("카페:")
        self.cafe_combo = QComboBox()
        self.cafe_combo.setMinimumWidth(250)  # 너비 축소
        self.cafe_combo.currentIndexChanged.connect(self.on_cafe_changed)

        # 게시판 선택
        board_label = QLabel("게시판:")
        self.board_combo = QComboBox()
        self.board_combo.setMinimumWidth(250)  # 너비 축소

        cafe_layout.addWidget(cafe_label)
        cafe_layout.addWidget(self.cafe_combo)
        cafe_layout.addSpacing(3)
        cafe_layout.addWidget(board_label)
        cafe_layout.addWidget(self.board_combo)
        cafe_group.setLayout(cafe_layout)

        # 체크박스 스타일 통일
        checkbox_style = """
            QCheckBox {
                color: white;
                spacing: 8px;
                min-height: 30px;
                min-width: 150px;
                padding: 5px 10px;
                background-color: #2b2b2b;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
            QCheckBox:hover {
                background-color: #353535;
                border: 1px solid #5c85d6;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #5c85d6;
                background: transparent;
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #5c85d6;
                background: #5c85d6;
                border-radius: 4px;
            }
        """

        # 이미지 설정 컨테이너
        image_container = QWidget()
        image_layout = QHBoxLayout(image_container)
        image_layout.setContentsMargins(0, 5, 0, 5)
        image_layout.setSpacing(10)
        
        # 이미지 첨부 설정
        self.use_image = QCheckBox("이미지 첨부")
        self.use_image.setStyleSheet(checkbox_style)
        self.use_image.toggled.connect(self.on_image_toggled)
        
        # 이미지 크기 설정
        self.image_size_widget = QWidget()
        image_size_layout = QHBoxLayout(self.image_size_widget)
        image_size_layout.setContentsMargins(0, 0, 0, 0)
        image_size_layout.setSpacing(5)
        
        # 이미지 크기 레이블
        self.image_size_label = QLabel("크기:")
        self.image_size_label.setStyleSheet("color: white; font-size: 12px;")
        
        # 이미지 너비 설정
        self.image_width = QSpinBox()
        self.image_width.setRange(50, 1200)
        self.image_width.setValue(400)
        self.image_width.setStyleSheet("""
            QSpinBox {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
                min-height: 25px;
            }
        """)
        
        # X 레이블
        self.x_label = QLabel("×")
        self.x_label.setStyleSheet("color: white; font-size: 12px;")
        
        # 이미지 높이 설정
        self.image_height = QSpinBox()
        self.image_height.setRange(50, 1200)
        self.image_height.setValue(400)
        self.image_height.setStyleSheet("""
            QSpinBox {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
                min-height: 25px;
            }
        """)
        
        # px 레이블
        self.px_label = QLabel("px")
        self.px_label.setStyleSheet("color: white; font-size: 12px;")
        
        # image_size_layout.addWidget(self.image_size_label)
        image_size_layout.addWidget(self.image_width)
        image_size_layout.addWidget(self.x_label)
        image_size_layout.addWidget(self.image_height)
        image_size_layout.addWidget(self.px_label)
        
        # 이미지 레이아웃에 추가
        image_layout.addWidget(self.use_image)
        image_layout.addWidget(self.image_size_widget)
        image_layout.addStretch()
        
        # 닉네임 변경 설정
        self.use_nickname = QCheckBox("닉네임 변경 사용")
        self.use_nickname.setChecked(True)
        self.use_nickname.setStyleSheet(checkbox_style)
        self.use_nickname.toggled.connect(self.on_nickname_toggled)
        
        # 닉네임 확인 버튼
        self.check_nickname_btn = QPushButton("닉네임 확인")
        self.check_nickname_btn.clicked.connect(self.show_nickname_dialog)
        self.check_nickname_btn.setStyleSheet("""
            QPushButton {
                background-color: #5c85d6;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #4a6fb8;
            }
        """)
        
        # 닉네임 관련 레이아웃
        nickname_layout = QHBoxLayout()
        nickname_layout.addWidget(self.use_nickname)
        nickname_layout.addWidget(self.check_nickname_btn)
        nickname_layout.addStretch()

        # 메인 레이아웃에 위젯 추가
        layout.addWidget(cafe_group)
        layout.addWidget(image_container)
        layout.addLayout(nickname_layout)
        layout.addStretch()
        self.setLayout(layout)
        
        # 초기 상태 설정
        self.on_nickname_toggled(self.use_nickname.isChecked())
        self.on_image_toggled(self.use_image.isChecked())

    def on_image_toggled(self, checked):
        """이미지 첨부 체크박스 토글 시 호출"""
        self.image_size_widget.setVisible(checked)
    
    def on_nickname_toggled(self, checked):
        """닉네임 변경 체크박스 토글 시 호출"""
        self.check_nickname_btn.setVisible(checked)
        
        if checked and not os.path.exists('nickname.txt'):
            # 닉네임 파일이 없으면 자동 생성
            generate_nicknames()
            QMessageBox.information(self, '알림', '닉네임 파일이 생성되었습니다. (1000개)')
    
    def show_nickname_dialog(self):
        """닉네임 확인 버튼 클릭 시 호출"""
        dialog = NicknameDialog(self)
        dialog.exec_()

    def update_cafe_list(self, cafe_list, headers):
        """카페 목록 업데이트"""
        self.current_headers = headers  # 헤더 정보 저장
        self.cafe_combo.clear()
        self.board_combo.clear()
        
        for cafe_id, cafe_url, cafe_name in cafe_list:
            self.cafe_combo.addItem(cafe_name, userData={'id': cafe_id, 'url': cafe_url})
            
        # 첫 번째 카페 선택
        if self.cafe_combo.count() > 0:
            self.cafe_combo.setCurrentIndex(0)
            self.on_cafe_changed(0)

    def on_cafe_changed(self, index):
        """카페 선택 시 게시판 목록 업데이트"""
        if index < 0 or not self.current_headers:
            return
            
        cafe_data = self.cafe_combo.currentData()
        if not cafe_data:
            return
            
        cafe_id = cafe_data['id']
        self.current_cafe_id = cafe_id
        
        # 게시판 목록 가져오기
        cafe_api = CafeAPI(self.current_headers)
        board_list = cafe_api.get_board_list(cafe_id)
        
        # 게시판 목록 업데이트
        self.board_combo.clear()
        if board_list:
            for board in board_list:
                self.board_combo.addItem(board['menu_name'], userData=board['menu_id'])

    def get_settings(self):
        """현재 설정값 반환"""
        return {
            'cafe_id': self.cafe_combo.currentData(),
            'cafe_name': self.cafe_combo.currentText(),
            'board_id': self.board_combo.currentData(),
            'board_name': self.board_combo.currentText(),
            'use_image': self.use_image.isChecked(),
            'image_width': self.image_width.value(),
            'image_height': self.image_height.value(),
            'use_nickname': self.use_nickname.isChecked()
        }

    def load_settings(self, settings):
        """설정값 로드"""
        # 카페 설정
        cafe_name = settings.get('cafe_name', '')
        index = self.cafe_combo.findText(cafe_name)
        if index >= 0:
            self.cafe_combo.setCurrentIndex(index)
        
        # 게시판 설정
        board = settings.get('board', '')
        index = self.board_combo.findText(board)
        if index >= 0:
            self.board_combo.setCurrentIndex(index)
        
        # 이미지 설정
        self.use_image.setChecked(settings.get('use_image', False))
        self.image_width.setValue(settings.get('image_width', 400))
        self.image_height.setValue(settings.get('image_height', 400))
        
        # 닉네임 설정
        self.use_nickname.setChecked(settings.get('use_nickname', True))

    def clear_settings(self):
        """설정 초기화"""
        self.cafe_combo.clear()
        self.board_combo.clear()
        self.use_image.setChecked(False)
        self.image_width.setValue(400)
        self.image_height.setValue(400)
        self.use_nickname.setChecked(True)
        self.current_headers = None
        self.current_cafe_id = None 
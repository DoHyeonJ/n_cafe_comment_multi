from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QLabel, 
                           QTextEdit, QHBoxLayout, QSpinBox, QCheckBox, QGroupBox)
from PyQt5.QtCore import Qt
from .cafe_widget import CafeWidget

class CommentSettingWidget(QWidget):
    def __init__(self, log):
        super().__init__()
        self.log = log
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 1. AI 프롬프트 설정
        prompt_group = QGroupBox("AI 프롬프트 설정")
        prompt_group.setStyleSheet("""
            QGroupBox {
                color: white;
                font-weight: bold;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
            }
        """)
        
        prompt_layout = QVBoxLayout()
        
        prompt_label = QLabel("AI에게 전달할 댓글 명령어를 입력하세요:")
        prompt_label.setStyleSheet("color: white;")
        
        self.prompt_text = QTextEdit()
        self.prompt_text.setPlaceholderText("예: 네이버 카페 게시글에 대한 자연스러운 댓글을 작성해주세요. 게시글의 내용을 참고하여 공감하는 내용으로 작성하되, 너무 길지 않게 2-3문장으로 작성해주세요.")
        self.prompt_text.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
                min-height: 100px;
            }
            QTextEdit:hover {
                border: 1px solid #5c85d6;
            }
        """)
        
        prompt_layout.addWidget(prompt_label)
        prompt_layout.addWidget(self.prompt_text)
        prompt_group.setLayout(prompt_layout)
        
        # 2. 댓글 간격 설정
        interval_group = QGroupBox("댓글 간격 설정")
        interval_group.setStyleSheet("""
            QGroupBox {
                color: white;
                font-weight: bold;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
            }
        """)
        
        interval_layout = QVBoxLayout()
        
        interval_desc = QLabel("계정별 댓글 작성 간격을 설정하세요 (초 단위):")
        interval_desc.setStyleSheet("color: white;")
        
        interval_input_layout = QHBoxLayout()
        
        interval_label = QLabel("기본 간격:")
        interval_label.setStyleSheet("color: white;")
        
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(10, 600)  # 10초 ~ 10분
        self.interval_spin.setValue(60)  # 기본값 60초
        self.interval_spin.setSuffix(" 초")
        self.interval_spin.setStyleSheet("""
            QSpinBox {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
                min-width: 80px;
            }
            QSpinBox:hover {
                border: 1px solid #5c85d6;
            }
        """)
        
        interval_range_label = QLabel("오차 범위(±):")
        interval_range_label.setStyleSheet("color: white;")
        
        self.interval_range_spin = QSpinBox()
        self.interval_range_spin.setRange(0, 120)  # 0초 ~ 2분
        self.interval_range_spin.setValue(15)  # 기본값 15초
        self.interval_range_spin.setSuffix(" 초")
        self.interval_range_spin.setStyleSheet("""
            QSpinBox {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 5px;
                min-width: 80px;
            }
            QSpinBox:hover {
                border: 1px solid #5c85d6;
            }
        """)
        
        interval_input_layout.addWidget(interval_label)
        interval_input_layout.addWidget(self.interval_spin)
        interval_input_layout.addWidget(interval_range_label)
        interval_input_layout.addWidget(self.interval_range_spin)
        interval_input_layout.addStretch()
        
        interval_layout.addWidget(interval_desc)
        interval_layout.addLayout(interval_input_layout)
        interval_group.setLayout(interval_layout)
        
        # 3. 주요 키워드 설정
        keyword_group = QGroupBox("주요 키워드 설정")
        keyword_group.setStyleSheet("""
            QGroupBox {
                color: white;
                font-weight: bold;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
            }
        """)
        
        keyword_layout = QVBoxLayout()
        
        self.use_keywords = QCheckBox("본문의 주요 키워드를 댓글에 랜덤하게 언급")
        self.use_keywords.setChecked(True)
        self.use_keywords.setStyleSheet("""
            QCheckBox {
                color: white;
                spacing: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                border: 1px solid #5c85d6;
                background: #2b2b2b;
            }
            QCheckBox::indicator:checked {
                border: 1px solid #5c85d6;
                background: #5c85d6;
            }
        """)
        
        keyword_desc = QLabel("AI가 게시글 본문에서 주요 키워드를 추출하여\n댓글에 자연스럽게 포함시킵니다.")
        keyword_desc.setStyleSheet("color: #aaaaaa; font-style: italic;")
        keyword_desc.setWordWrap(True)
        
        keyword_layout.addWidget(self.use_keywords)
        keyword_layout.addWidget(keyword_desc)
        keyword_group.setLayout(keyword_layout)
        
        # 메인 레이아웃에 추가
        layout.addWidget(prompt_group)
        layout.addWidget(interval_group)
        layout.addWidget(keyword_group)
        layout.addStretch()
        
        self.setLayout(layout)
        
        # 초기 간격 정보 업데이트
        self.update_interval_info()
    
    def update_interval_info(self):
        """댓글 간격 정보 업데이트"""
        # 랜덤 범위 표시 제거
        pass
    
    def get_settings(self):
        """댓글 설정 정보 반환"""
        # 댓글 간격 계산
        interval_base = self.interval_spin.value()
        interval_range = self.interval_range_spin.value()
        interval_min = max(0, interval_base - interval_range)
        interval_max = interval_base + interval_range
        
        return {
            'prompt': self.prompt_text.toPlainText(),
            'interval': {
                'base': interval_base,
                'range': interval_range,
                'min': interval_min,
                'max': interval_max
            },
            'use_keywords': self.use_keywords.isChecked()
        }
    
    def load_settings(self, settings):
        """설정값 로드"""
        # AI 프롬프트 설정
        self.prompt_text.setPlainText(settings.get('prompt', ''))
        
        # 댓글 간격 설정
        interval = settings.get('interval', {})
        self.interval_spin.setValue(interval.get('base', 60))
        self.interval_range_spin.setValue(interval.get('range', 15))
        
        # 주요 키워드 설정
        self.use_keywords.setChecked(settings.get('use_keywords', True))

class ScriptTab(QWidget):
    def __init__(self, log):
        super().__init__()
        self.log = log
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # 설정 탭 위젯
        settings_tab = QTabWidget()
        settings_tab.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #3d3d3d;
                background: #2b2b2b;
            }
            QTabBar::tab {
                background: #353535;
                color: #cccccc;
                padding: 8px 12px;
                border: 1px solid #3d3d3d;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: #2b2b2b;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background: #404040;
            }
        """)
        
        # 카페 설정
        self.cafe_widget = CafeWidget(self.log)
        
        # 댓글 설정
        self.comment_widget = CommentSettingWidget(self.log)
        
        # 탭에 위젯 추가
        settings_tab.addTab(self.cafe_widget, "카페 설정")
        settings_tab.addTab(self.comment_widget, "댓글 설정")
        
        layout.addWidget(settings_tab)
        self.setLayout(layout)
        
    def get_current_settings(self):
        """현재 설정 정보 반환"""
        return {
            'cafe': self.cafe_widget.get_settings(),
            'comment': self.comment_widget.get_settings()
        }
    
    def load_account_settings(self, account_id):
        """선택된 계정의 설정 로드"""
        # 나중에 구현
        pass
    
    def save_account_settings(self, account_id):
        """현재 설정을 선택된 계정에 저장"""
        # 나중에 구현
        pass
    
    def load_task_settings(self, task_id):
        """작업의 설정값을 UI에 로드"""
        # 나중에 구현
        pass
    
    def save_task_settings(self, task_id):
        """현재 UI 설정값을 작업에 저장"""
        # 나중에 구현
        pass
    
    def load_settings(self, settings):
        """설정값 로드"""
        if not settings:
            return
            
        # 카페 설정 로드
        cafe_settings = settings.get('cafe', {})
        self.cafe_widget.load_settings(cafe_settings)
        
        # 댓글 설정 로드
        comment_settings = settings.get('comment', {})
        self.comment_widget.load_settings(comment_settings) 
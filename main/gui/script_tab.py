from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QCheckBox, QHBoxLayout)
from .cafe_widget import CafeWidget
from .content_widget import ContentWidget
from .reply_widget import ReplySettingWidget

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
        
        # 콘텐츠 설정
        self.content_widget = ContentWidget(self.log)
        
        # 댓글 설정
        self.reply_widget = ReplySettingWidget(self.log)
        
        # 체크박스 스타일 통일
        checkbox_style = """
            QCheckBox {
                color: white;
                spacing: 8px;
                min-height: 30px;
                min-width: 120px;
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
        
        # 이미지 첨부 체크박스
        self.use_image = QCheckBox("이미지 첨부")
        self.use_image.setStyleSheet(checkbox_style)
        
        # 닉네임 변경 체크박스
        self.use_nickname = QCheckBox("닉네임 변경")
        self.use_nickname.setStyleSheet(checkbox_style)
        
        # 체크박스 레이아웃
        checkbox_layout = QHBoxLayout()
        checkbox_layout.addWidget(self.use_image)
        checkbox_layout.addWidget(self.use_nickname)
        checkbox_layout.addStretch()
        
        # 탭 추가
        settings_tab.addTab(self.cafe_widget, "카페 설정")
        settings_tab.addTab(self.content_widget, "콘텐츠 설정")
        settings_tab.addTab(self.reply_widget, "댓글 설정")
        
        layout.addWidget(settings_tab)
        self.setLayout(layout)

    def get_current_settings(self):
        """현재 모든 설정값 반환"""
        return {
            'cafe': {
                'cafe_id': self.cafe_widget.cafe_combo.currentData(),
                'cafe_name': self.cafe_widget.cafe_combo.currentText(),
                'cafe_url': self.cafe_widget.cafe_combo.currentData(),
                'board_id': self.cafe_widget.board_combo.currentData(),
                'board_name': self.cafe_widget.board_combo.currentText(),
                'use_image': self.cafe_widget.use_image.isChecked(),
                'use_nickname': self.cafe_widget.use_nickname.isChecked()
            },
            'content': {
                'prompt': self.content_widget.prompt.toPlainText(),
                'min_length': self.content_widget.min_length.value(),
                'max_length': self.content_widget.max_length.value(),
                'use_content_collection': self.content_widget.use_content_collection.isChecked(),
                'content_collection_count': self.content_widget.content_collection_count.value()
            },
            'reply': {
                'use_reply': self.reply_widget.use_reply.isChecked(),
                'use_nickname': self.reply_widget.use_nickname.isChecked(),
                'account': {
                    'id': self.reply_widget.id_input.text(),
                    'pw': self.reply_widget.pw_input.text()
                },
                'scenario': self.reply_widget.scenario
            }
        }

    def load_account_settings(self, account_id):
        # 선택된 계정의 설정 로드
        pass

    def save_account_settings(self, account_id):
        # 현재 설정을 선택된 계정에 저장
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
        
        # 콘텐츠 설정 로드
        content_settings = settings.get('content', {})
        self.content_widget.load_settings(content_settings)
        
        # 댓글 설정 로드
        reply_settings = settings.get('reply', {})
        self.reply_widget.load_settings(reply_settings) 
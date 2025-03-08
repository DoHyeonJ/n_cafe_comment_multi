from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QLabel)
from .cafe_widget import CafeWidget

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
        
        # 댓글 설정 (빈 공간으로 변경)
        self.reply_widget = QWidget()
        reply_layout = QVBoxLayout()
        reply_layout.addWidget(QLabel("댓글 설정 영역 - 추후 구현 예정"))
        self.reply_widget.setLayout(reply_layout)
        
        # 탭에 위젯 추가
        settings_tab.addTab(self.cafe_widget, "카페 설정")
        settings_tab.addTab(self.reply_widget, "댓글 설정")
        
        layout.addWidget(settings_tab)
        self.setLayout(layout)

    def get_current_settings(self):
        """현재 설정 정보 반환"""
        return {
            'cafe': self.cafe_widget.get_settings(),
            'reply': {}  # 빈 댓글 설정
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
        
        # 댓글 설정은 빈 위젯이므로 로드하지 않음 
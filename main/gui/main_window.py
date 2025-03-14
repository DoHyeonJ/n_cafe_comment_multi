from PyQt5.QtWidgets import (QMainWindow, QWidget, QGridLayout, 
                           QVBoxLayout, QGroupBox, QHBoxLayout, 
                           QLabel, QPushButton, QMessageBox,
                           QListWidgetItem, QApplication, QProgressDialog,
                           QInputDialog, QListWidget, QTabWidget, QDialog,
                           QProgressBar, QFileDialog, QFormLayout, QScrollArea,
                           QMenu, QAction)
from PyQt5.QtCore import Qt, QSize, QTimer
from PyQt5.QtGui import QIcon, QFontMetrics, QDesktopServices
from .script_tab import ScriptTab
from .routine_tab import RoutineTab
from ..utils.log import Log
from ..utils.licence import Licence
from .styles import DARK_STYLE
from .account_widget import AccountWidget
from ..api.cafe import CafeAPI
from .settings_dialog import SettingsDialog
from .task_settings_dialog import TaskSettingsDialog
from ..utils.settings_manager import SettingsManager
from ..api.auth import NaverAuth
from ..worker import Worker
import time
import os
from PyQt5.QtCore import QUrl
import sys

class TaskDetailDialog(QDialog):
    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task
        self.init_ui()
        
    def init_ui(self):
        # 대화상자 설정
        self.setWindowTitle(f"작업 #{self.task['id']} 상세 정보")
        self.setMinimumSize(700, 450)  # 높이 줄임
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
                color: white;
            }
            QLabel {
                color: white;
            }
            QGroupBox {
                color: white;
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
            }
        """)
        
        # 메인 레이아웃
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 기본 정보 그룹
        basic_group = QGroupBox("기본 정보")
        basic_layout = QFormLayout()
        basic_layout.setContentsMargins(15, 20, 15, 15)
        basic_layout.setSpacing(10)
        
        # 계정 정보
        account_count = len(self.task.get('all_accounts', []))
        self.account_label = QLabel(f"{account_count}개 계정")
        
        # 계정 목록 대화상자 버튼
        self.show_accounts_btn = QPushButton("계정 목록 보기")
        self.show_accounts_btn.setStyleSheet("""
            QPushButton {
                background-color: #5c85d6;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #4a6fb8;
            }
        """)
        self.show_accounts_btn.clicked.connect(self.show_accounts_dialog)
        
        # 계정 컨테이너
        account_container = QWidget()
        account_layout = QHBoxLayout()  # 가로 배치로 변경
        account_layout.setContentsMargins(0, 0, 0, 0)
        account_layout.setSpacing(10)
        account_layout.addWidget(self.account_label)
        account_layout.addWidget(self.show_accounts_btn)
        account_container.setLayout(account_layout)
        
        # 카페 및 게시판 정보
        cafe_info = self.task['cafe_info']
        board_info = self.task['board_info']
        cafe_label = QLabel(f"{cafe_info['cafe_name']}")
        board_label = QLabel(f"{board_info['board_name']}")
        
        # 기본 정보 추가
        basic_layout.addRow("계정:", account_container)
        basic_layout.addRow("카페:", cafe_label)
        basic_layout.addRow("게시판:", board_label)
        basic_group.setLayout(basic_layout)
        
        # 작업 설정 그룹
        task_group = QGroupBox("작업 설정")
        task_layout = QFormLayout()
        task_layout.setContentsMargins(15, 20, 15, 15)
        task_layout.setSpacing(10)
        
        # 작업 설정 정보
        cafe_settings = self.task['cafe_settings']
        post_count = cafe_settings.get('post_count', 0)
        comment_min = cafe_settings.get('comment_count', {}).get('min', 0)
        comment_max = cafe_settings.get('comment_count', {}).get('max', 0)
        like_min = cafe_settings.get('like_count', {}).get('min', 0)
        like_max = cafe_settings.get('like_count', {}).get('max', 0)
        
        # 작업 설정 추가
        task_layout.addRow("게시글 수집:", QLabel(f"{post_count}개"))
        task_layout.addRow("댓글 작업:", QLabel(f"{comment_min}~{comment_max}개 (랜덤)"))
        task_layout.addRow("좋아요 작업:", QLabel(f"{like_min}~{like_max}개 (랜덤)"))
        task_group.setLayout(task_layout)
        
        # 댓글 설정 그룹
        comment_group = QGroupBox("댓글 설정")
        comment_layout = QFormLayout()
        comment_layout.setContentsMargins(15, 20, 15, 15)
        comment_layout.setSpacing(10)
        
        # 댓글 설정 정보
        comment_settings = self.task['comment_settings']
        interval = comment_settings.get('interval', {})
        interval_min = interval.get('min', 0)
        interval_max = interval.get('max', 0)
        use_keywords = '사용' if comment_settings.get('use_keywords', False) else '미사용'
        prevent_duplicate = '사용' if comment_settings.get('prevent_duplicate', True) else '미사용'
        
        # 프롬프트 목록
        prompts = comment_settings.get('prompts', [])
        prompt_count = len(prompts)
        
        # 프롬프트 대화상자 버튼
        self.show_prompts_btn = QPushButton("AI 프롬프트 보기")
        self.show_prompts_btn.setStyleSheet("""
            QPushButton {
                background-color: #5c85d6;
                color: white;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #4a6fb8;
            }
        """)
        self.show_prompts_btn.clicked.connect(self.show_prompts_dialog)
        
        # 프롬프트 컨테이너
        prompt_container = QWidget()
        prompt_layout = QHBoxLayout()  # 가로 배치로 변경
        prompt_layout.setContentsMargins(0, 0, 0, 0)
        prompt_layout.setSpacing(10)
        prompt_layout.addWidget(QLabel(f"{prompt_count}개 등록됨"))
        prompt_layout.addWidget(self.show_prompts_btn)
        prompt_container.setLayout(prompt_layout)
        
        # 댓글 설정 추가
        comment_layout.addRow("댓글 간격:", QLabel(f"{interval_min}~{interval_max}초 (랜덤)"))
        comment_layout.addRow("키워드 사용:", QLabel(use_keywords))
        comment_layout.addRow("중복 방지:", QLabel(prevent_duplicate))
        comment_layout.addRow("AI 프롬프트:", prompt_container)
        comment_group.setLayout(comment_layout)
        
        # 확인 버튼
        close_btn = QPushButton("확인")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #5c85d6;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                min-width: 100px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a6fb8;
            }
        """)
        close_btn.clicked.connect(self.accept)
        
        # 레이아웃에 위젯 추가
        main_layout.addWidget(basic_group)
        main_layout.addWidget(task_group)
        main_layout.addWidget(comment_group)
        main_layout.addWidget(close_btn, alignment=Qt.AlignCenter)
        
        self.setLayout(main_layout)
    
    def show_accounts_dialog(self):
        """계정 목록을 별도의 대화상자로 표시"""
        accounts = self.task.get('all_accounts', [])
        if not accounts:
            QMessageBox.information(self, "계정 목록", "등록된 계정이 없습니다.")
            return
            
        # 계정 목록 대화상자 생성
        dialog = QDialog(self)
        dialog.setWindowTitle("계정 목록")
        dialog.setMinimumSize(300, 400)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
                color: white;
            }
            QLabel {
                color: white;
            }
            QListWidget {
                background-color: #333;
                color: white;
                border: 1px solid #555;
                border-radius: 3px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #444;
            }
            QListWidget::item:selected {
                background-color: #4a6fb8;
            }
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
        
        # 레이아웃 설정
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # 계정 수 표시
        count_label = QLabel(f"총 {len(accounts)}개 계정")
        count_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(count_label)
        
        # 계정 목록 위젯
        account_list = QListWidget()
        for account in accounts:
            account_list.addItem(account)
        layout.addWidget(account_list)
        
        # 닫기 버튼
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def show_prompts_dialog(self):
        """프롬프트 목록을 별도의 대화상자로 표시"""
        prompts = self.task['comment_settings'].get('prompts', [])
        if not prompts:
            QMessageBox.information(self, "AI 프롬프트", "등록된 프롬프트가 없습니다.")
            return
            
        # 프롬프트 목록 대화상자 생성
        dialog = QDialog(self)
        dialog.setWindowTitle("AI 프롬프트 목록")
        dialog.setMinimumSize(500, 400)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
                color: white;
            }
            QLabel {
                color: white;
            }
            QScrollArea {
                border: 1px solid #555;
                background-color: #333;
            }
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
        
        # 레이아웃 설정
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # 프롬프트 수 표시
        count_label = QLabel(f"총 {len(prompts)}개 프롬프트")
        count_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(count_label)
        
        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        # 프롬프트 컨테이너
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(10, 10, 10, 10)
        container_layout.setSpacing(10)
        
        # 프롬프트 목록 추가
        for i, prompt in enumerate(prompts, 1):
            prompt_frame = QWidget()
            prompt_frame.setStyleSheet("background-color: #3a3a3a; border-radius: 4px;")
            
            prompt_layout = QVBoxLayout()
            prompt_layout.setContentsMargins(10, 10, 10, 10)
            
            # 프롬프트 번호
            number_label = QLabel(f"프롬프트 #{i}")
            number_label.setStyleSheet("color: #aaa; font-size: 12px;")
            
            # 프롬프트 내용
            content_label = QLabel(prompt)
            content_label.setWordWrap(True)
            content_label.setStyleSheet("color: #ddd; padding: 5px 0;")
            
            prompt_layout.addWidget(number_label)
            prompt_layout.addWidget(content_label)
            prompt_frame.setLayout(prompt_layout)
            
            container_layout.addWidget(prompt_frame)
        
        container_layout.addStretch()
        container.setLayout(container_layout)
        scroll.setWidget(container)
        
        layout.addWidget(scroll)
        
        # 닫기 버튼
        close_btn = QPushButton("닫기")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
        
        dialog.setLayout(layout)
        dialog.exec_()

class TaskListItem(QWidget):
    def __init__(self, task_name, task_info, task_number, parent=None):
        super().__init__(parent)
        self.task_info = task_info  # 작업 정보 저장
        self.task_number = task_number  # 작업 번호 저장
        
        # 클릭 가능한 스타일 설정
        self.setStyleSheet("""
            QWidget {
                background-color: #2d2d2d;
                border-radius: 4px;
            }
            QWidget:hover {
                background-color: #3a3a3a;
                cursor: pointer;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(12)
        
        # 왼쪽 상태 표시 바 & 번호
        left_container = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(2)
        
        # 작업 번호
        self.number_label = QLabel(f"#{task_number}")
        self.number_label.setStyleSheet("""
            color: #5c85d6;
            font-size: 14px;
            font-weight: bold;
        """)
        
        # 상태 표시 바
        self.status_bar = QWidget()
        self.status_bar.setFixedWidth(4)
        self.status_bar.setMinimumHeight(40)
        self.status_bar.setStyleSheet("""
            background-color: #5c85d6;
            border-radius: 2px;
        """)
        
        left_layout.addWidget(self.number_label, alignment=Qt.AlignCenter)
        left_layout.addWidget(self.status_bar, alignment=Qt.AlignCenter)
        left_container.setLayout(left_layout)
        
        # 중앙 정보 영역
        info_container = QWidget()
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(4)
        
        # 계정 및 카페 정보
        account_cafe_layout = QHBoxLayout()
        account_cafe_layout.setContentsMargins(0, 0, 0, 0)
        account_cafe_layout.setSpacing(15)  # 간격 증가
        
        # 계정 정보 - 개수만 표시
        account_count = task_info.get('account_count', 1)
        self.account_label = QLabel(f"계정: {account_count}개")
        self.account_label.setStyleSheet("""
            color: white;
            font-size: 13px;
            font-weight: bold;
        """)
        
        # 카페/게시판 정보 통합 - 각각 5글자로 제한
        cafe_name = self.limit_text(task_info['cafe_name'], 10)
        board_name = self.limit_text(task_info['board_name'], 10)
        cafe_board_text = f"카페/게시판: {cafe_name}/{board_name}"
        
        self.cafe_board_label = QLabel(cafe_board_text)
        self.cafe_board_label.setStyleSheet("""
            color: white;
            font-size: 13px;
        """)
        self.cafe_board_label.setToolTip(f"{task_info['cafe_name']}/{task_info['board_name']}")  # 전체 텍스트를 툴팁으로 표시
        
        account_cafe_layout.addWidget(self.account_label)
        account_cafe_layout.addWidget(self.cafe_board_label)
        account_cafe_layout.addStretch()
        
        # 정보 레이아웃에 추가
        info_layout.addLayout(account_cafe_layout)
        info_container.setLayout(info_layout)
        
        # 레이아웃에 위젯 추가
        layout.addWidget(left_container)
        layout.addWidget(info_container, stretch=1)
        self.setLayout(layout)
        
        # 상태에 따른 스타일 설정
        self.update_status_style(task_info['status'])
    
    def limit_text(self, text, max_length):
        """텍스트 길이 제한 함수"""
        if len(text) > max_length:
            return text[:max_length] + "..."
        return text
    
    def update_status_style(self, status):
        """상태에 따른 스타일 업데이트"""
        if status == '실행 중':
            self.status_bar.setStyleSheet("background-color: #4CAF50; border-radius: 2px;")
        elif status == '완료':
            self.status_bar.setStyleSheet("background-color: #2196F3; border-radius: 2px;")
        elif status == '오류':
            self.status_bar.setStyleSheet("background-color: #F44336; border-radius: 2px;")
        elif status == '일시정지':
            self.status_bar.setStyleSheet("background-color: #FFC107; border-radius: 2px;")
        else:  # 대기 중
            self.status_bar.setStyleSheet("background-color: #5c85d6; border-radius: 2px;")
    
    def set_post_url(self, url, title=None):
        """게시글 URL 설정"""
        # 상태 업데이트만 수행
        self.update_status_style('완료')
        
    def sizeHint(self):
        """위젯 크기 힌트"""
        return QSize(0, 45)  # 너비를 0으로 설정하여 부모 위젯에 맞추도록 함

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 로그 초기화
        self.log = Log()
        
        # 라이선스 초기화
        self.licence = Licence()
        
        # 계정 정보 초기화
        self.accounts = {}  # 계정 정보 저장 딕셔너리
        
        # 작업 목록 초기화
        self.tasks = []  # 작업 목록
        self.next_task_id = 1  # 다음 작업 ID
        
        # 작업 실행 상태
        self.is_running = False
        self.workers = []  # 워커 목록
        
        # 시그널 연결 상태 추적
        self.task_list_click_connected = False
        
        # 모니터링 위젯 생성
        self.monitor_widget = RoutineTab(self.log)
        
        # 모니터링 위젯 시그널 연결
        self.monitor_widget.add_task_clicked.connect(self.add_task)
        self.monitor_widget.remove_task_clicked.connect(self.remove_task)
        self.monitor_widget.remove_all_clicked.connect(self.remove_all_tasks)
        self.monitor_widget.execute_tasks_clicked.connect(self.run_tasks)
        
        # 라이선스 확인
        if not self.check_and_create_license():
            self.handle_missing_license()
            return
            
        # UI 초기화
        self.init_ui()

    def check_and_create_license(self):
        """라이선스 파일을 체크하고 없으면 생성하는 함수"""
        try:
            # 라이선스 파일이 없는 경우
            if not os.path.exists('licence.json'):
                return self.handle_missing_license()

            # 라이선스 파일이 있는 경우 유효성 검사
            licence_key = self.licence.get_licence_key()
            is_valid, message = self.licence.check_license(licence_key)

            if not is_valid:
                # 유효하지 않은 라이선스인 경우
                QMessageBox.warning(self, '라이선스 오류', f'라이선스가 유효하지 않습니다.\n{message}')
                
                # 라이선스 파일 삭제
                if os.path.exists('licence.json'):
                    os.remove('licence.json')
                
                # 다시 라이선스 입력 처리
                return self.handle_missing_license()

            # 라이선스가 만료된 경우
            if self.licence.is_expired():
                QMessageBox.critical(self, '라이선스 만료', '라이선스가 만료되었습니다.\n라이선스를 연장하시기 바랍니다.')
                QDesktopServices.openUrl(QUrl("https://do-hyeon.tistory.com/pages/%EB%9D%BC%EC%9D%B4%EC%84%A0%EC%8A%A4-%EA%B5%AC%EB%A7%A4%EC%97%B0%EC%9E%A5-%EA%B0%80%EC%9D%B4%EB%93%9C"))
                return False

            return True

        except Exception as e:
            QMessageBox.critical(self, '오류', '알 수 없는 오류가 발생하였습니다.\n프로그램을 다시 실행해주세요.')
            self.log.add_log(f"라이선스 확인 중 오류 발생: {str(e)}", "red")
            return False

    def handle_missing_license(self):
        """라이선스가 없는 경우 처리"""
        while True:
            input_dialog = QInputDialog(self)
            input_dialog.setWindowTitle('라이선스 키 입력')
            input_dialog.setLabelText('라이선스 키를 입력해주세요:')
            input_dialog.resize(400, 200)
            
            ok = input_dialog.exec_()
            licence_key = input_dialog.textValue().strip()
            
            if not ok:
                return False
                
            if not licence_key:
                QMessageBox.warning(self, '경고', '라이선스 키를 입력해주세요.')
                continue
            
            # 라이선스 유효성 검사
            is_valid, message = self.licence.check_license(licence_key)
            
            if is_valid:
                # 라이선스 정보 저장
                if self.licence.save_licence(licence_key, message):
                    QMessageBox.information(self, '알림', '유효한 라이선스가 확인되었습니다.')
                    return True
                else:
                    QMessageBox.warning(self, '오류', '라이선스 저장 중 오류가 발생했습니다.')
                    continue
            else:
                retry = QMessageBox.question(
                    self,
                    '라이선스 오류',
                    f'유효하지 않은 라이선스입니다.\n사유: {message}\n\n다시 시도하시겠습니까?',
                    QMessageBox.Yes | QMessageBox.No
                )
                if retry == QMessageBox.No:
                    return False
                    
        return False

    def init_ui(self):
        # 메인 위젯 생성
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # 메인 레이아웃 설정 (좌우 분할)
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)
        
        # 좌측 영역 (계정 관리 + 설정)
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_widget.setLayout(left_layout)
        
        # 계정 관리 영역 (좌측 상단)
        account_group = QGroupBox("계정 관리")
        account_layout = QVBoxLayout()
        account_group.setLayout(account_layout)
        
        # 계정 위젯 생성
        self.account_widget = AccountWidget(self.log, self.monitor_widget)
        account_layout.addWidget(self.account_widget)
        
        # 계정 위젯 시그널 연결
        self.account_widget.login_success.connect(self.on_login_success)
        self.account_widget.account_added.connect(self.add_account_to_list)
        self.account_widget.account_removed.connect(self.remove_account_from_list)
        self.account_widget.account_selected.connect(self.on_account_selected)
        
        # 설정 영역 (좌측 하단)
        settings_group = QGroupBox("설정")
        settings_layout = QVBoxLayout()
        settings_group.setLayout(settings_layout)
        
        # 설정 탭 위젯 생성
        self.settings_tab = ScriptTab(self.log)
        settings_layout.addWidget(self.settings_tab)
        
        # 좌측 레이아웃에 위젯 추가 (비율 6:4)
        left_layout.addWidget(account_group, 6)
        left_layout.addWidget(settings_group, 4)
        
        # 우측 영역 (모니터링/작업)
        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_widget.setLayout(right_layout)
        
        # 모니터링 영역
        monitor_group = QGroupBox("모니터링")
        monitor_layout = QVBoxLayout()
        monitor_group.setLayout(monitor_layout)
        
        # 모니터링 위젯 추가
        monitor_layout.addWidget(self.monitor_widget)
        
        # 우측 레이아웃에 모니터링 그룹 추가
        right_layout.addWidget(monitor_group)
        
        # 메인 레이아웃에 좌우 위젯 추가 (비율 5:5)
        main_layout.addWidget(left_widget, 5)
        main_layout.addWidget(right_widget, 5)
        
        # 메뉴바 생성
        self.create_menu_bar()
        
        # 윈도우 설정
        self.setWindowTitle("네이버 카페 댓글 프로그램")
        self.setGeometry(100, 100, 1200, 900)
        self.setStyleSheet(DARK_STYLE)

    def create_menu_bar(self):
        """메뉴바 생성"""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #2b2b2b;
                color: white;
                border-bottom: 1px solid #3d3d3d;
            }
            QMenuBar::item {
                background-color: transparent;
                padding: 8px 12px;
            }
            QMenuBar::item:selected {
                background-color: #3d3d3d;
            }
            QMenu {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #3d3d3d;
            }
            QMenu::item {
                padding: 8px 20px;
            }
            QMenu::item:selected {
                background-color: #3d3d3d;
            }
        """)
        
        # 파일 메뉴
        file_menu = menubar.addMenu('파일')
        
        # 작업 설정 관리 메뉴
        task_settings_action = QAction('작업 설정 관리', self)
        task_settings_action.triggered.connect(self.show_task_settings_dialog)
        file_menu.addAction(task_settings_action)
        
        # 구분선
        file_menu.addSeparator()
        
        # 종료 메뉴
        exit_action = QAction('종료', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 도움말 메뉴
        help_menu = menubar.addMenu('도움말')
        
        # 라이선스 정보 메뉴
        license_action = QAction('라이선스 정보', self)
        license_action.triggered.connect(self.show_license_info)
        help_menu.addAction(license_action)
        
        # 프로그램 정보 메뉴
        about_action = QAction('프로그램 정보', self)
        about_action.triggered.connect(self.show_about_info)
        help_menu.addAction(about_action)

    def show_task_settings_dialog(self):
        """작업 설정 관리 대화상자 표시"""
        dialog = TaskSettingsDialog(self)
        dialog.exec_()
        
    def show_license_info(self):
        """라이선스 정보 표시"""
        license_key = self.licence.get_licence_key()
        expiry_date = self.licence.get_expiry_date()
        
        message = f"""
라이선스 정보:
- 라이선스 키: {license_key}
- 만료일: {expiry_date}
        """
        
        QMessageBox.information(self, "라이선스 정보", message)
        
    def show_about_info(self):
        """프로그램 정보 표시"""
        message = """
네이버 카페 댓글 프로그램 v1.0

© 2023 All Rights Reserved.
        """
        
        QMessageBox.information(self, "프로그램 정보", message)

    def show_settings_dialog(self):
        """설정 관리 대화상자 표시"""
        dialog = SettingsDialog(self.settings_manager, self)
        dialog.setStyleSheet(DARK_STYLE)
        dialog.exec_()

    def get_all_settings(self):
        """현재 모든 설정값 반환 - 계정 목록과 작업 목록만 저장"""
        return {
            'accounts': self.get_accounts_settings(),
            'tasks': self.tasks
        }
    
    def get_accounts_settings(self):
        """계정 설정 정보 반환 - 기본 정보만 저장"""
        accounts_data = {}
        for account_id, account_info in self.accounts.items():
            accounts_data[account_id] = {
                'pw': account_info['pw']
                # cafe_list는 저장하지 않음
                # headers는 저장하지 않음 (보안 이슈)
            }
        return accounts_data
    
    def apply_settings(self, settings_data):
        """불러온 설정 적용"""
        # 계정 정보 복원 전에 로그인 필요 여부 확인
        accounts_to_login = []
        
        if 'accounts' in settings_data:
            # 첫 번째 계정만 로그인 검증
            first_account = None
            
            for account_id, account_info in settings_data['accounts'].items():
                # 첫 번째 계정 저장
                if first_account is None:
                    first_account = (account_id, account_info['pw'])
                    
                    # 첫 번째 계정이 이미 있는지 확인
                    if account_id in self.accounts:
                        # 헤더 정보가 유효한지 확인
                        if not self.is_header_valid(self.accounts[account_id].get('headers', {})):
                            accounts_to_login.append((account_id, account_info['pw']))
                    else:
                        # 새 계정은 로그인 필요
                        accounts_to_login.append((account_id, account_info['pw']))
        
        # 로그인이 필요한 계정이 있으면 사용자에게 알림
        if accounts_to_login:
            accounts_str = "\n".join([f"• {acc[0]}" for acc in accounts_to_login])
            reply = QMessageBox.question(
                self,
                '계정 로그인 필요',
                f'첫 번째 계정의 로그인이 필요합니다:\n\n{accounts_str}\n\n'
                f'로그인을 진행하시겠습니까? (설정 불러오기를 완료하려면 필요합니다)',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.No:
                return False  # 설정 적용 취소
        
        # 기존 데이터 초기화
        old_accounts = self.accounts.copy()
        self.accounts = {}
        self.tasks = []
        
        # 계정 위젯의 계정 목록 초기화
        self.account_widget.account_list.clear()
        self.account_widget.verified_accounts.clear()
        self.account_widget.account_passwords.clear()
        
        # 계정 정보 복원
        if 'accounts' in settings_data:
            for account_id, account_info in settings_data['accounts'].items():
                # 기존 계정의 헤더 정보가 유효한 경우 유지
                headers = {}
                if account_id in old_accounts and self.is_header_valid(old_accounts[account_id].get('headers', {})):
                    headers = old_accounts[account_id]['headers']
                    self.log.info(f"계정 '{account_id}'의 기존 헤더 정보를 유지합니다.")
                
                # 계정 추가
                self.accounts[account_id] = {
                    'pw': account_info['pw'],
                    'headers': headers,
                    'cafe_list': old_accounts.get(account_id, {}).get('cafe_list', [])
                }
                
                # UI에 계정 추가
                self.account_widget.account_list.addItem(account_id)
                # 계정 비밀번호도 AccountWidget에 저장
                self.account_widget.account_passwords[account_id] = account_info['pw']
                
        # 작업 목록 복원
        if 'tasks' in settings_data:
            self.tasks = settings_data['tasks']
        self.update_task_list()
        
        # 로그인 필요한 계정들에 대해 로그인 진행 (첫 번째 계정만)
        if accounts_to_login:
            self.log.info(f"첫 번째 계정에 대해 로그인을 진행합니다...")
            
            # 로그인 진행 상태 대화상자
            progress_dialog = QProgressDialog("계정 로그인 중입니다...", "취소", 0, 1, self)
            progress_dialog.setWindowTitle("로그인 진행 중")
            progress_dialog.setWindowModality(Qt.WindowModal)
            progress_dialog.setAutoClose(True)
            progress_dialog.setAutoReset(True)
            progress_dialog.setCancelButton(None)  # 취소 버튼 비활성화
            progress_dialog.setMinimumDuration(0)  # 즉시 표시
            progress_dialog.show()
            
            login_success_count = 0
            
            # 첫 번째 계정만 로그인
            account_id, password = accounts_to_login[0]
            
            # 진행 상태 업데이트
            progress_dialog.setValue(0)
            progress_dialog.setLabelText(f"계정 '{account_id}' 로그인 중...")
            QApplication.processEvents()  # UI 업데이트
            
            # 로그인 시도
            auth = NaverAuth()
            auth.set_credentials(account_id, password)
            success = auth.login()
            
            if success:
                # 로그인 성공 시 헤더 정보 업데이트
                headers = auth.get_headers()
                self.accounts[account_id]['headers'] = headers
                
                # 카페 목록 로드
                self.load_cafe_list(account_id, headers)
                login_success_count += 1
                
                # 검증된 계정 목록에 추가
                self.account_widget.verified_accounts.add(account_id)
                
                # 계정 아이템 스타일 업데이트
                items = self.account_widget.account_list.findItems(account_id, Qt.MatchExactly)
                if items:
                    items[0].setForeground(Qt.green)
                    items[0].setText(f"{account_id} ✓")  # 체크 표시 추가
                
                self.log.info(f"계정 '{account_id}' 로그인 성공")
            else:
                self.log.error(f"계정 '{account_id}' 로그인 실패")
            
            # 진행 대화상자 완료 및 닫기
            progress_dialog.setValue(1)
            progress_dialog.close()
            
            # 로그인 결과 알림
            if login_success_count > 0:
                QMessageBox.information(
                    self,
                    '로그인 완료',
                    f'첫 번째 계정의 로그인이 완료되었습니다.'
                )
            else:
                QMessageBox.warning(
                    self,
                    '로그인 실패',
                    f'첫 번째 계정의 로그인에 실패했습니다.\n'
                    f'해당 계정은 수동으로 다시 로그인해주세요.'
                )
        
        # 첫 번째 계정 선택
        if self.account_widget.account_list.count() > 0:
            self.account_widget.account_list.setCurrentRow(0)
            first_account = self.account_widget.account_list.item(0).text().split(' ')[0]  # ✓ 마크 제거
            self.on_account_selected(first_account)  # 첫 번째 계정의 카페 목록 로드
        
        self.log.info("설정이 성공적으로 적용되었습니다.")
        return True

    def on_login_progress(self, message, color):
        """로그인 진행상황 업데이트"""
        self.log.add_log(message, color)
        self.monitor_widget.add_log_message({'message': message, 'color': color})
    
    def on_account_login_finished(self, success, headers, account_id):
        """계정 선택 시 로그인 완료 처리"""
        if success:
            # 계정 정보에 헤더 설정
            self.accounts[account_id]['headers'] = headers
            
            # 카페 목록 로드
            self.load_cafe_list(account_id, headers)
            
            self.log.info(f'계정 {account_id} 로그인 성공')
        else:
            self.log.error(f'계정 {account_id} 로그인 실패')
            QMessageBox.warning(self, '로그인 실패', f'계정 "{account_id}"의 로그인에 실패했습니다.\n다른 계정을 선택해주세요.')

    def add_account_to_list(self, account_id, password):
        """계정 목록에 계정 추가"""
        if account_id in self.accounts:
            # 이미 존재하는 계정은 건너뜁니다
            return
        
        # 계정 정보 초기화 (헤더는 로그인 성공 시그널에서 설정됨)
        self.accounts[account_id] = {
            'pw': password,
            'headers': None,
            'cafe_list': []
        }
        
        self.log.info(f'계정 추가됨: {account_id}')
    
    def on_login_success(self, headers):
        """로그인 성공 시 호출 (AccountWidget에서 발생한 시그널)"""
        # 현재 선택된 계정 ID 가져오기
        if self.account_widget.account_list.currentItem():
            account_id = self.account_widget.account_list.currentItem().text().split(' ')[0]  # ✓ 마크 제거
            
            # 계정 정보에 헤더 설정
            if account_id in self.accounts:
                self.accounts[account_id]['headers'] = headers
                
                # 카페 목록 로드
                self.load_cafe_list(account_id, headers)
                
                self.log.info(f'계정 로그인 성공: {account_id}')

    def load_cafe_list(self, account_id, headers):
        """계정의 카페 목록 로드"""
        if not self.is_header_valid(headers):
            self.log.error(f'계정 {account_id}의 로그인 정보가 유효하지 않습니다.')
            return
            
        # 카페 API 생성
        cafe_api = CafeAPI(headers)
        
        # 카페 목록 로드
        try:
            cafe_list = cafe_api.get_cafe_list()
            
            # 계정 정보에 카페 목록 저장
            self.accounts[account_id]['cafe_list'] = cafe_list
            
            # 카페 위젯 업데이트
            self.settings_tab.cafe_widget.update_cafe_list(cafe_list, headers)
            
            self.log.info(f'카페 목록 로드 완료 ({len(cafe_list)}개)')
        except Exception as e:
            self.log.error(f'카페 목록 로드 중 오류 발생: {str(e)}')
            QMessageBox.warning(self, '카페 목록 로드 실패', f'카페 목록을 불러오는 중 오류가 발생했습니다.\n{str(e)}')

    def on_account_selected(self, account_id):
        """계정 선택 시 호출"""
        if account_id not in self.accounts:
            return
        
        # 체크 마크가 있는 경우 제거
        account_id = account_id.split(' ')[0]
        
        # 카페 설정 업데이트
        if self.accounts[account_id]['headers'] is not None and self.accounts[account_id]['cafe_list']:
            self.settings_tab.cafe_widget.update_cafe_list(
                self.accounts[account_id]['cafe_list'], 
                self.accounts[account_id]['headers']
            )
        elif self.accounts[account_id]['headers'] is not None:
            self.load_cafe_list(account_id, self.accounts[account_id]['headers'])
        else:
            # 로그인되지 않은 계정인 경우 카페 목록 초기화 (빈 목록으로 업데이트)
            self.settings_tab.cafe_widget.update_cafe_list([], None)
            self.log.info(f"계정 '{account_id}'는 아직 검증되지 않았습니다. 검증 버튼을 눌러 로그인을 시도해주세요.")

    def remove_task(self):
        """선택된 작업 삭제"""
        if not self.monitor_widget.task_list.currentItem():
            QMessageBox.warning(self, '경고', '삭제할 작업을 선택해주세요.')
            return
            
        current_item = self.monitor_widget.task_list.currentItem()
        task_idx = self.monitor_widget.task_list.currentRow()
        
        # 작업 ID 확인 (UserRole에 저장된 데이터)
        task_id = current_item.data(Qt.UserRole)
        
        # ID로 작업 찾기
        task_to_remove = None
        for i, task in enumerate(self.tasks):
            if task['id'] == task_id:
                task_to_remove = i
                break
        
        if task_to_remove is not None:
            # 작업 정보 저장
            removed_task = self.tasks[task_to_remove]
            account_id = removed_task['account_id']
            cafe_name = removed_task['cafe_info']['cafe_name']
            board_name = removed_task['board_info']['board_name']
            
            # 삭제 확인 대화상자
            reply = QMessageBox.question(
                self,
                '작업 삭제 확인',
                f'작업 #{task_id}을(를) 삭제하시겠습니까?\n\n계정: {account_id}\n카페: {cafe_name}\n게시판: {board_name}',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No  # 기본값은 No
            )
            
            if reply == QMessageBox.Yes:
                # 작업 삭제
                self.tasks.pop(task_to_remove)
                self.monitor_widget.task_list.takeItem(task_idx)
                
                # 작업 ID 재할당
                for i, task in enumerate(self.tasks, 1):
                    task['id'] = i
                
                # UI 업데이트
                self.update_task_list()
                
                # 로그 메시지
                msg = f'작업 #{task_id} 삭제됨: 계정 {account_id}, 카페 {cafe_name}, 게시판 {board_name}'
                self.log.info(msg)
                self.monitor_widget.add_log_message({'message': msg, 'color': 'red'})

    def view_task_settings(self, task_id):
        """작업 설정 보기"""
        # 작업 찾기
        task = None
        for t in self.tasks:
            if t['id'] == task_id:
                task = t
                break
                
        if not task:
            return
            
        # 작업 정보 메시지 생성
        cafe_info = task['cafe_info']
        board_info = task['board_info']
        cafe_settings = task['cafe_settings']
        comment_settings = task['comment_settings']
        
        # 계정 정보 형식 설정
        account_count = len(task.get('all_accounts', []))
        account_display = f"{account_count}개 계정"
        
        # 댓글 간격 정보
        interval = comment_settings.get('interval', {})
        interval_min = interval.get('min', 0)
        interval_max = interval.get('max', 0)
        
        # 프롬프트 목록 정보
        prompts = comment_settings.get('prompts', [])
        prompt_count = len(prompts)
        
        # 프롬프트 예시 (첫 번째 프롬프트만 표시, 너무 길면 잘라서 표시)
        prompt_example = ""
        if prompt_count > 0:
            prompt_example = prompts[0]
            if len(prompt_example) > 100:
                prompt_example = prompt_example[:100] + "..."
        
        message = f"""
[기본 정보]
- 계정: {account_display}
- 카페: {cafe_info['cafe_name']}
- 게시판: {board_info['board_name']}

[작업 설정]
- 게시글 수집: {cafe_settings.get('post_count', 0)}개
- 댓글 작업: {cafe_settings.get('comment_count', {}).get('min', 0)}~{cafe_settings.get('comment_count', {}).get('max', 0)}개 (랜덤)
- 좋아요 작업: {cafe_settings.get('like_count', {}).get('min', 0)}~{cafe_settings.get('like_count', {}).get('max', 0)}개 (랜덤)

[댓글 설정]
- 댓글 간격: {interval_min}~{interval_max}초 (랜덤)
- 키워드 사용: {'사용' if comment_settings.get('use_keywords', False) else '미사용'}
- 중복 방지: {'사용' if comment_settings.get('prevent_duplicate', True) else '미사용'}
- AI 프롬프트: {prompt_count}개 등록됨
"""
        
        # 프롬프트 예시 추가 (있는 경우에만)
        if prompt_example:
            message += f"\n[프롬프트 예시]\n{prompt_example}"
        
        # 메시지 박스 표시
        QMessageBox.information(self, f"작업 {task_id} 설정", message)

    def remove_account_from_list(self, account_id):
        """계정 목록에서 계정 삭제"""
        if account_id in self.accounts:
            # 현재 선택된 아이템의 인덱스 저장
            current_row = self.account_widget.account_list.currentRow()
            
            # 계정 삭제
            self.accounts.pop(account_id)
            items = self.account_widget.account_list.findItems(account_id, Qt.MatchExactly)
            for item in items:
                self.account_widget.account_list.takeItem(self.account_widget.account_list.row(item))
            
            # 해당 계정의 작업 삭제 여부 확인
            account_tasks = [t for t in self.tasks if t['account_id'] == account_id]
            if account_tasks:
                reply = QMessageBox.question(
                    self, 
                    '계정 작업 삭제 확인',
                    f'이 계정에 연결된 {len(account_tasks)}개의 작업이 있습니다. 함께 삭제하시겠습니까?',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # 해당 계정의 작업 삭제
                    self.tasks = [t for t in self.tasks if t['account_id'] != account_id]
                    # 작업 ID 재할당
                    for i, task in enumerate(self.tasks, 1):
                        task['id'] = i
                    # UI 업데이트
                    self.update_task_list()
            
            # 카페 설정 초기화
            self.settings_tab.cafe_widget.update_cafe_list([], None)
            
            # 다음 계정 선택 (있는 경우)
            next_row = min(current_row, self.account_widget.account_list.count() - 1)
            if next_row >= 0:
                next_item = self.account_widget.account_list.item(next_row)
                if next_item:
                    self.account_widget.account_list.setCurrentItem(next_item)
                    next_account_id = next_item.text().split(' ')[0]  # ✓ 또는 ✗ 마크 제거
                    account = self.accounts[next_account_id]
                    
                    # 다음 계정의 카페 목록 로드
                    if account['cafe_list']:
                        self.settings_tab.cafe_widget.update_cafe_list(account['cafe_list'], account['headers'])
                    else:
                        self.load_cafe_list(next_account_id, account['headers'])
        
            self.log.info(f'계정 삭제됨: {account_id}')

    def update_task_list(self):
        """작업 목록 UI 업데이트"""
        # 작업 목록 초기화
        self.monitor_widget.task_list.clear()
        
        # 작업이 없는 경우 메시지 표시
        if not self.tasks:
            self.monitor_widget.task_count_label.setText("등록된 작업이 없습니다.")
            return
        
        # 작업 목록 업데이트
        for task in self.tasks:
            # 계정 개수 계산
            account_count = len(task.get('all_accounts', []))
            
            # 작업 정보 생성
            task_info = {
                'account_count': account_count,  # 계정 개수 추가
                'cafe_name': task['cafe_info']['cafe_name'],
                'board_name': task['board_info']['board_name'],
                'status': task.get('status', '대기 중'),
                'progress': task.get('progress', 0),
                'completed_count': task.get('completed_count', 0),
                'error_count': task.get('error_count', 0)
            }
            
            # 작업 항목 생성
            item = QListWidgetItem(self.monitor_widget.task_list)
            task_widget = TaskListItem("", task_info, task['id'])
            item.setSizeHint(task_widget.sizeHint())
            item.setData(Qt.UserRole, task['id'])  # 작업 ID 저장
            
            # 작업 항목 추가
            self.monitor_widget.task_list.addItem(item)
            self.monitor_widget.task_list.setItemWidget(item, task_widget)
        
        # 작업 개수 업데이트
        self.monitor_widget.task_count_label.setText(f"총 {len(self.tasks)}개의 작업")
        
        # 작업 항목 클릭 시 상세 정보 표시 이벤트 연결 (한 번만 연결)
        if not self.task_list_click_connected:
            self.monitor_widget.task_list.itemClicked.connect(self.show_task_detail)
            self.task_list_click_connected = True

    def show_task_detail(self, item):
        """작업 항목 클릭 시 상세 정보 표시"""
        # 작업 ID 가져오기
        task_id = item.data(Qt.UserRole)
        
        # 작업 찾기
        task = None
        for t in self.tasks:
            if t['id'] == task_id:
                task = t
                break
                
        if not task:
            return
            
        # 상세 정보 대화상자 표시
        detail_dialog = TaskDetailDialog(task, self)
        detail_dialog.exec_()

    def on_tasks_reordered(self, parent, start, end, destination, row):
        """작업 순서 변경 처리"""
        # 작업 순서 변경 전에 현재 상태 저장
        old_tasks = self.tasks.copy()
        
        # 작업 순서 변경
        if start < len(self.tasks):
            task = self.tasks.pop(start)
            if row > len(self.tasks):
                self.tasks.append(task)
            else:
                self.tasks.insert(row, task)
            
            # 작업 ID 재할당
            for i, task in enumerate(self.tasks, 1):
                task['id'] = i
            
            # UI 업데이트 (딜레이 추가)
            QTimer.singleShot(100, self.update_task_list)
            
            msg = f'작업 순서가 변경되었습니다'
            self.monitor_widget.add_log_message({'message': msg, 'color': 'blue'})

    def remove_all_tasks(self):
        """모든 작업 삭제"""
        task_count = len(self.tasks)
        
        if task_count == 0:
            QMessageBox.information(self, '알림', '삭제할 작업이 없습니다.')
            return
            
        reply = QMessageBox.question(
            self, 
            '전체 작업 삭제 확인',
            f'정말 모든 작업을 삭제하시겠습니까?\n\n총 작업 수: {task_count}개',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No  # 기본값은 No
        )
        
        if reply == QMessageBox.Yes:
            # 모든 작업 삭제
            self.tasks.clear()
            self.monitor_widget.task_list.clear()
            
            # 작업 개수 업데이트
            self.monitor_widget.task_count_label.setText(f"총 0개의 작업")
            
            msg = f'모든 작업이 삭제되었습니다 ({task_count}개)'
            self.monitor_widget.add_log_message({'message': msg, 'color': 'red'})

    def save_script(self):
        """현재 설정된 모든 계정과 작업 설정을 저장"""
        self.show_settings_dialog()

    def load_script(self):
        """저장된 설정을 불러와서 UI에 적용"""
        self.show_settings_dialog()

    def is_header_valid(self, headers):
        """헤더 정보가 유효한지 확인 (12시간 이내)"""
        if not headers or '_timestamp' not in headers:
            return False
            
        # 현재 시간과 헤더 생성 시간의 차이 계산 (초 단위)
        time_diff = time.time() - headers['_timestamp']
        
        # 12시간 = 43200초
        return time_diff < 43200 

    def get_all_tasks(self):
        """현재 작업 리스트 전체를 반환합니다.
        
        Returns:
            list: 모든 작업 정보가 담긴 리스트
        """
        return self.tasks
        
    def run_tasks(self, is_running):
        """작업 실행 또는 중지
        
        Args:
            is_running (bool): 실행 상태 (True: 실행, False: 중지)
        """
        if is_running:
            # 작업 리스트가 비어있는지 확인
            if not self.tasks:
                # 로그 모니터에만 메시지 표시
                self.monitor_widget.add_log_message({
                    'message': '실행할 작업이 없습니다. 작업 실행이 중지됩니다.',
                    'color': 'red'
                })
                # 실행 상태를 False로 설정하고 버튼 상태 직접 변경
                self.monitor_widget.is_running = False
                # toggle_execution 호출하지 않고 버튼 상태 직접 변경
                self.monitor_widget.execute_btn.setText("실행")
                self.monitor_widget.execute_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 10px;
                        font-size: 14px;
                        min-height: 40px;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                """)
                return
                
            # 작업 실행 로그 추가
            msg = f'작업 실행 시작: 총 {len(self.tasks)}개 작업'
            self.monitor_widget.add_log_message({'message': msg, 'color': 'green'})
            
            # 작업 상태 초기화 및 로깅
            for i, task in enumerate(self.tasks):
                # 작업 상태 초기화
                task['status'] = 'pending'
                self.monitor_widget.add_log_message({
                    'message': f"작업 #{i+1} (ID: {task.get('id', '알 수 없음')}) 상태 초기화: pending",
                    'color': 'blue'
                })
            
            # Worker 클래스 인스턴스 생성 및 작업 실행
            if not hasattr(self, 'worker') or not self.worker.isRunning():
                self.worker = Worker(main_window=self)  # MainWindow 인스턴스 전달
                self.worker.set_tasks(self.tasks)
                
                # 작업 간격 설정 가져오기
                min_interval = self.monitor_widget.min_interval.value()
                max_interval = self.monitor_widget.max_interval.value()
                self.worker.set_intervals(min_interval, max_interval)
                
                # 시그널 연결
                self.worker.task_completed.connect(self.on_task_completed)
                self.worker.task_error.connect(self.on_task_error)
                self.worker.log_message.connect(self.on_log_message)
                self.worker.post_completed.connect(self.on_post_completed)
                self.worker.next_task_info.connect(self.on_next_task_info)  # 다음 작업 정보 시그널 연결
                self.worker.all_tasks_completed.connect(self.on_all_tasks_completed)  # 모든 작업 완료 시그널 연결
                
                # 별도의 스레드에서 작업 실행
                self.worker.start()  # QThread.start() 호출 - 비동기 실행
            else:
                # 이미 실행 중인 경우 로그 추가
                self.monitor_widget.add_log_message({
                    'message': '이미 작업이 실행 중입니다.',
                    'color': 'yellow'
                })
        else:
            # 작업 중지 로그 추가
            msg = '작업 실행 중지 요청'
            self.monitor_widget.add_log_message({'message': msg, 'color': 'red'})
            
            # Worker 중지
            if hasattr(self, 'worker') and self.worker.isRunning() and self.worker.is_running:
                self.worker.stop()
                self.monitor_widget.add_log_message({
                    'message': '작업 중지 요청이 전송되었습니다.',
                    'color': 'yellow'
                })
            else:
                self.monitor_widget.add_log_message({
                    'message': '중지할 작업이 없습니다.',
                    'color': 'yellow'
                })
                # 버튼 상태 되돌리기
                self.monitor_widget.execute_btn.setText("실행")
                self.monitor_widget.execute_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 10px;
                        font-size: 14px;
                        min-height: 40px;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                """)

    def on_task_completed(self, task):
        """작업 완료 시 호출되는 메서드"""
        # 작업 완료 로그 추가
        self.monitor_widget.add_log_message({
            'message': f"작업 완료: ID {task.get('id', '알 수 없음')}, 상태: {task.get('status', '알 수 없음')}",
            'color': 'green'
        })
        
        # 작업 상태 로깅 (모든 작업 완료 여부 확인은 Worker에서 처리)
        task_id = task.get('id', '알 수 없음')
        task_status = task.get('status', '알 수 없음')
        
        self.monitor_widget.add_log_message({
            'message': f"작업 #{task_id} 상태 변경: {task_status}",
            'color': 'blue'
        })
            
    def on_task_error(self, task, error_msg):
        """작업 오류 발생 시 호출되는 메서드"""
        # 작업 오류 로그 추가
        self.monitor_widget.add_log_message({
            'message': f"작업 오류: ID {task.get('id', '알 수 없음')}, 상태: {task.get('status', '알 수 없음')}",
            'color': 'red'
        })
        
        # 오류 메시지 로깅
        self.monitor_widget.add_log_message({
            'message': f"오류 내용: {error_msg}",
            'color': 'red'
        })
        
        # 작업 상태 로깅 (모든 작업 완료 여부 확인은 Worker에서 처리)
        task_id = task.get('id', '알 수 없음')
        task_status = task.get('status', '알 수 없음')
        
        self.monitor_widget.add_log_message({
            'message': f"작업 #{task_id} 상태 변경: {task_status}",
            'color': 'blue'
        })

    def on_log_message(self, message_data):
        """Worker에서 전송한 로그 메시지 처리"""
        self.monitor_widget.add_log_message(message_data)
        
    def on_post_completed(self, post_info):
        """게시글 등록 완료 시 호출되는 메서드
        
        Args:
            post_info (dict): 게시글 정보
        """
        # # 게시글 정보 로그 추가
        # self.monitor_widget.add_log_message({
        #     'message': f"📝 게시글 등록 완료: {post_info['title']}",
        #     'color': 'green'
        # })
        
        # 게시글 URL 로그 추가
        # self.monitor_widget.add_log_message({
        #     'message': f"🔗 게시글 URL: {post_info['url']}",
        #     'color': 'blue'
        # })
        
        # 게시글 정보 업데이트 (task_list에서 해당 작업 찾아서 상태 표시 업데이트)
        # if post_info.get('task'):
        #     task_id = post_info['task'].get('id')
        #     if task_id:
        #         # 작업 목록에서 해당 작업 찾기
        #         for i in range(self.monitor_widget.task_list.count()):
        #             item = self.monitor_widget.task_list.item(i)
        #             if item and item.data(Qt.UserRole) == task_id:
        #                 # 작업 위젯 가져오기
        #                 task_widget = self.monitor_widget.task_list.itemWidget(item)
        #                 if task_widget:
        #                     # 게시글 URL 설정 및 표시
        #                     task_widget.set_post_url(post_info['url'], post_info['title'])
        #                     break 
        pass

    def set_ai_api_key(self, api_key):
        """AI API 키 설정
        
        Args:
            api_key (str): API 키
        """
        self.ai_api_key = api_key
        self.log.info("AI API 키가 설정되었습니다.")

    def on_next_task_info(self, info):
        """다음 작업 정보 수신 시 호출되는 메서드
        
        Args:
            info (dict): 다음 작업 정보
                - next_task_number (int): 다음 작업 번호
                - next_execution_time (str): 다음 실행 시간
                - wait_time (str): 대기 시간
        """
        # 모니터 위젯에 다음 작업 정보 표시
        self.monitor_widget.update_next_task_info(info)

    def on_all_tasks_completed(self, is_normal_completion):
        """모든 작업이 완료되었을 때 호출되는 메서드
        
        Args:
            is_normal_completion (bool): 정상 완료 여부 (True: 정상 완료, False: 중간 중지)
        """
        # 작업 완료 로그 추가
        if is_normal_completion:
            self.monitor_widget.add_log_message({
                'message': "[작업 완료] 모든 작업이 정상적으로 완료되었습니다.",
                'color': 'green'
            })
            
            # 작업 반복 모드 확인
            repeat_mode = self.monitor_widget.repeat_checkbox.isChecked()
            self.log.info(f"작업 반복 모드: {repeat_mode}")
            
            # 작업 리스트가 비어있는지 확인
            if repeat_mode and self.tasks:
                self.log.info("작업 반복 모드가 활성화되어 있습니다. 작업을 다시 시작합니다.")
                
                # Worker 상태 정리
                if hasattr(self, 'worker'):
                    self.log.info("기존 Worker 객체를 정리합니다.")
                    self.worker.is_running = False
                    if self.worker.isRunning():
                        self.worker.wait(1000)
                    del self.worker
                
                # 대기 시간 계산 (5초 후 재시작)
                wait_time = 5
                self.log.info(f"{wait_time}초 후 작업을 다시 시작합니다.")
                self.monitor_widget.add_log_message({
                    'message': f"[작업 반복] {wait_time}초 후 작업을 다시 시작합니다.",
                    'color': 'blue'
                })
                
                # 타이머를 사용하여 일정 시간 후 작업 재시작
                QTimer.singleShot(wait_time * 1000, self.restart_tasks)
                return
            elif repeat_mode and not self.tasks:
                self.log.info("작업 반복 모드가 활성화되어 있지만, 작업 리스트가 비어있어 재시작하지 않습니다.")
                self.monitor_widget.add_log_message({
                    'message': "[작업 반복 중지] 작업 리스트가 비어있어 반복 실행을 중지합니다.",
                    'color': 'red'
                })
        else:
            self.monitor_widget.add_log_message({
                'message': "[작업 중지] 작업이 중간에 중지되었습니다.",
                'color': 'yellow'
            })
        
        # Worker 상태 업데이트 및 정리
        if hasattr(self, 'worker'):
            self.log.info("Worker 상태를 False로 설정하고 정리합니다.")
            self.worker.is_running = False
            
            # Worker 스레드가 실행 중인 경우 대기
            if self.worker.isRunning():
                self.log.info("Worker 스레드가 종료될 때까지 대기합니다.")
                self.worker.wait(1000)  # 최대 1초 대기
                
            # Worker 객체 정리
            self.log.info("Worker 객체를 정리합니다.")
            if hasattr(self, 'worker'):
                del self.worker
        
        # 실행 버튼 상태 변경 (이미 변경되지 않은 경우에만)
        if self.monitor_widget.is_running:
            self.log.info("실행 버튼으로 변경합니다.")
            self.monitor_widget.is_running = False  # 직접 상태 변경
            self.monitor_widget.execute_btn.setText("실행")
            self.monitor_widget.execute_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 10px;
                    font-size: 14px;
                    min-height: 40px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            self.log.info(f"버튼 상태 변경 완료: is_running = {self.monitor_widget.is_running}")
        else:
            self.log.info("버튼이 이미 실행 상태입니다. 상태 변경이 필요하지 않습니다.")
            
        # 다음 작업 정보 초기화
        self.monitor_widget.next_task_label.setText("대기 중...")
        self.log.info("다음 작업 정보가 초기화되었습니다.")

    def restart_tasks(self):
        """작업을 다시 시작하는 메서드 (작업 반복 모드에서 사용)"""
        self.log.info("작업을 다시 시작합니다.")
        
        # 작업 리스트가 비어있는지 확인
        if not self.tasks:
            self.log.info("작업 리스트가 비어있어 재시작하지 않습니다.")
            self.monitor_widget.add_log_message({
                'message': "[작업 반복 중지] 작업 리스트가 비어있어 반복 실행을 중지합니다.",
                'color': 'red'
            })
            
            # 실행 버튼 상태가 실행 상태인 경우 중지 상태로 변경
            if self.monitor_widget.is_running:
                self.log.info("버튼 상태를 중지 상태로 변경합니다.")
                self.monitor_widget.is_running = False  # 직접 상태 변경
                self.monitor_widget.execute_btn.setText("실행")
                self.monitor_widget.execute_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #4CAF50;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 10px;
                        font-size: 14px;
                        min-height: 40px;
                    }
                    QPushButton:hover {
                        background-color: #45a049;
                    }
                """)
                self.log.info(f"버튼 상태 변경 완료: is_running = {self.monitor_widget.is_running}")
            return
        
        # 버튼이 이미 실행 상태인 경우 중지 상태로 변경
        if not self.monitor_widget.is_running:
            self.log.info("버튼 상태를 실행 상태로 변경합니다.")
            # toggle_execution 호출하지 않고 버튼 상태 직접 변경
            self.monitor_widget.is_running = True
            self.monitor_widget.execute_btn.setText("중지")
            self.monitor_widget.execute_btn.setStyleSheet("""
                QPushButton {
                    background-color: #d65c5c;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 10px;
                    font-size: 14px;
                    min-height: 40px;
                }
                QPushButton:hover {
                    background-color: #b84a4a;
                }
            """)
        
        # 작업 실행
        self.run_tasks(True)

    def add_task(self):
        """작업 추가"""
        # 계정 선택 확인
        if not self.account_widget.account_list.currentItem():
            QMessageBox.warning(self, '경고', '계정을 먼저 선택해주세요.')
            return
            
        # 현재 선택된 계정 ID
        selected_account_id = self.account_widget.account_list.currentItem().text().split(' ')[0]  # ✓ 마크 제거
        
        # 선택된 계정 로그인 확인
        if selected_account_id not in self.accounts or self.accounts[selected_account_id]['headers'] is None:
            QMessageBox.warning(self, '경고', '선택한 계정이 로그인되지 않았습니다.\n계정 검증 후 다시 시도해주세요.')
            return
            
        # 카페 선택 확인
        selected_cafe = self.settings_tab.cafe_widget.get_selected_cafe()
        if not selected_cafe:
            QMessageBox.warning(self, '경고', '카페를 선택해주세요.')
            return
            
        # 게시판 선택 확인
        selected_board = self.settings_tab.cafe_widget.get_selected_board()
        if not selected_board:
            # 게시판이 선택되지 않은 경우, 첫 번째 게시판을 선택
            if self.settings_tab.cafe_widget.board_combo.count() > 0:
                self.settings_tab.cafe_widget.board_combo.setCurrentIndex(0)
                selected_board = self.settings_tab.cafe_widget.get_selected_board()
                if not selected_board:
                    QMessageBox.warning(self, '경고', '게시판을 선택해주세요.')
                    return
            else:
                QMessageBox.warning(self, '경고', '게시판을 선택해주세요.')
                return
            
        # 카페 설정 가져오기
        cafe_settings = self.settings_tab.cafe_widget.get_settings()
        
        # IP 테더링 정보 제외
        if 'use_ip_tethering' in cafe_settings:
            del cafe_settings['use_ip_tethering']
        if 'ip_verified' in cafe_settings:
            del cafe_settings['ip_verified']
        
        # 댓글 설정 가져오기 (프롬프트 목록과 중복방지 설정 포함)
        full_comment_settings = self.settings_tab.comment_widget.get_settings()
        
        # 댓글 프롬프트 확인
        if not full_comment_settings.get('prompts') or len(full_comment_settings.get('prompts', [])) == 0:
            reply = QMessageBox.question(
                self,
                'AI 프롬프트 확인',
                'AI 프롬프트가 등록되지 않았습니다. 계속 진행하시겠습니까?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        # 작업 ID 생성
        task_id = len(self.tasks) + 1
        
        # 모든 계정 정보 수집 (검증 여부와 관계없이 모든 계정)
        all_accounts = list(self.accounts.keys())
        
        # 작업 정보 생성
        task_info = {
            'id': task_id,
            'account_id': selected_account_id,  # 주 계정 ID
            'all_accounts': all_accounts,  # 모든 계정 ID 목록
            'cafe_info': selected_cafe,
            'board_info': selected_board,
            'cafe_settings': cafe_settings,
            'comment_settings': full_comment_settings,  # 전체 댓글 설정 사용
            'status': '대기 중',
            'progress': 0,
            'completed_count': 0,
            'error_count': 0,
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'last_updated': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 계정 수 계산
        account_count = len(all_accounts)
        account_display = f"{account_count}개 계정"
        
        # 작업 목록에 추가
        self.tasks.append(task_info)
        
        # 작업 목록 UI 업데이트
        self.update_task_list()
        
        # 로그 메시지
        msg = f'작업 추가됨: 계정 {account_display}, 카페 {selected_cafe["cafe_name"]}, 게시판 {selected_board["board_name"]}'
        self.log.info(msg)
        self.monitor_widget.add_log_message({'message': msg, 'color': 'blue'})
        
        # 작업 추가 성공 메시지
        QMessageBox.information(self, '작업 추가 완료', f'작업 #{task_id}이(가) 성공적으로 추가되었습니다.')
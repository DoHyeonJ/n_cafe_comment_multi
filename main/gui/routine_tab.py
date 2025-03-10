from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QGroupBox, QLabel, 
                           QListWidget, QSpinBox, QLineEdit, QTableWidget, QHeaderView, QTableWidgetItem, QTabWidget, QCheckBox, QTextEdit, QMessageBox)
from .monitor_widget import RoutineMonitorWidget, BaseMonitorWidget
from .styles import DARK_STYLE
from datetime import datetime
from PyQt5.QtCore import Qt, pyqtSignal
from main.api.ai_generator import AIGenerator
from ..utils.log import Log

class RoutineTab(BaseMonitorWidget):
    add_task_clicked = pyqtSignal()  # 작업 추가 시그널
    remove_task_clicked = pyqtSignal()  # 작업 삭제 시그널
    remove_all_clicked = pyqtSignal()  # 전체 삭제 시그널
    execute_tasks_clicked = pyqtSignal(bool)  # 작업 실행/정지 시그널, 실행 상태를 전달
    
    def __init__(self, log: Log):
        super().__init__(log)
        self.is_running = False  # 실행 상태
        self.api_key_validated = False  # API 키 검증 상태
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # 다음 작업 정보 표시 영역 추가
        next_task_info = QGroupBox("다음 작업 정보")
        next_task_layout = QHBoxLayout()
        
        self.next_task_label = QLabel("대기 중...")
        self.next_task_label.setStyleSheet("""
            QLabel {
                color: #5c85d6;
                font-size: 13px;
                padding: 10px;
                background-color: #2b2b2b;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
        """)
        
        next_task_layout.addWidget(self.next_task_label)
        next_task_info.setLayout(next_task_layout)
        
        # 탭 위젯 (상단)
        tab_widget = QTabWidget()
        tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #3d3d3d;
                background: #2b2b2b;
            }
            QTabBar::tab {
                background: #353535;
                color: #cccccc;
                padding: 5px 10px;  /* 탭 크기 축소 */
                border: 1px solid #3d3d3d;
                border-bottom: none;
                min-width: 80px;  /* 최소 너비 설정 */
                max-width: 120px;  /* 최대 너비 설정 */
            }
            QTabBar::tab:selected {
                background: #2b2b2b;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background: #404040;
            }
        """)
        
        # 1. 작업 관리 탭 (작업 목록 + 작업 설정)
        task_manage_tab = QWidget()
        task_layout = QVBoxLayout()
        task_layout.setSpacing(10)
        
        # 작업 목록과 버튼
        task_list_container = QWidget()
        task_list_layout = QVBoxLayout(task_list_container)
        task_list_layout.setContentsMargins(0, 0, 0, 0)
        task_list_layout.setSpacing(5)
        
        # 작업 목록
        self.task_list = QListWidget()
        self.task_list.setDragDropMode(QListWidget.InternalMove)
        self.task_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.task_list.setStyleSheet("""
            QListWidget {
                background-color: #2b2b2b;
                border: 1px solid #3d3d3d;
                border-radius: 6px;
                padding: 5px;
            }
            QListWidget::item {
                background-color: #353535;
                border-radius: 6px;
                margin: 2px;
                min-height: 50px;  /* 아이템 높이 더 축소 */
            }
            QListWidget::item:selected {
                background-color: #404040;
                border: 1px solid #5c85d6;
            }
            QListWidget::item:hover:!selected {
                background-color: #383838;
                border: 1px solid #4a4a4a;
            }
            QListWidget::item:drag {
                background-color: #2b2b2b;
                border: 1px solid #5c85d6;
                opacity: 0.8;
            }
        """)
        
        # 작업 순서 변경 시그널 연결
        self.task_list.model().rowsMoved.connect(self.on_tasks_reordered)
        
        # 작업 개수 표시 레이블
        self.task_count_label = QLabel("총 0개의 작업")
        self.task_count_label.setStyleSheet("""
            color: #808080;
            font-size: 12px;
            padding: 5px;
            border-top: 1px solid #3d3d3d;
        """)
        self.task_count_label.setAlignment(Qt.AlignRight)
        
        task_list_layout.addWidget(self.task_list)
        task_list_layout.addWidget(self.task_count_label)
        
        # 작업 추가/삭제 버튼
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)  # 버튼 간격 증가
        
        # 버튼 기본 스타일에 크기 관련 설정 추가
        btn_base_style = """
            QPushButton {
                min-width: 120px;  /* 버튼 최소 너비 */
                padding: 10px 20px;  /* 패딩 증가 */
                font-size: 13px;  /* 폰트 크기 증가 */
            }
        """
        
        # 각 버튼 스타일 업데이트
        add_btn_style = btn_base_style + """
            QPushButton {
                background-color: #5c85d6;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4a6fb8;
            }
        """
        
        remove_btn_style = btn_base_style + """
            QPushButton {
                background-color: #d65c5c;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #b84a4a;
            }
        """
        
        remove_all_btn_style = btn_base_style + """
            QPushButton {
                background-color: #8B0000;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #A00000;
            }
        """
        
        self.add_task_btn = QPushButton("작업 추가")
        self.remove_task_btn = QPushButton("작업 삭제")
        self.remove_all_btn = QPushButton("전체 삭제")  # 전체 삭제 버튼 추가
        self.remove_task_btn.setEnabled(True)
        self.remove_all_btn.setEnabled(True)
        
        self.add_task_btn.setStyleSheet(add_btn_style)
        self.remove_task_btn.setStyleSheet(remove_btn_style)
        self.remove_all_btn.setStyleSheet(remove_all_btn_style)
        
        # 버튼 클릭 이벤트 연결
        self.add_task_btn.clicked.connect(self.add_task_clicked.emit)
        self.remove_task_btn.clicked.connect(self.remove_task_clicked.emit)
        self.remove_all_btn.clicked.connect(self.remove_all_clicked.emit)  # 시그널 연결
        
        # 작업 선택 시 삭제 버튼 활성화/비활성화
        self.task_list.itemSelectionChanged.connect(self.on_task_selection_changed)
        
        btn_layout.addWidget(self.add_task_btn, stretch=1)
        btn_layout.addWidget(self.remove_task_btn, stretch=1)
        btn_layout.addWidget(self.remove_all_btn, stretch=1)
        
        # 작업 관리 탭에 추가
        task_layout.addWidget(task_list_container)
        task_layout.addLayout(btn_layout)
        task_manage_tab.setLayout(task_layout)
        
        # 작업 설정 영역
        settings_group = QGroupBox("작업 설정")
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(10)
        
        # 실행 설정 컨테이너 (간격 + 반복)
        execution_container = QWidget()
        execution_layout = QHBoxLayout(execution_container)
        execution_layout.setContentsMargins(0, 0, 0, 0)
        
        # 실행 간격 설정
        interval_group = QWidget()
        interval_layout = QHBoxLayout(interval_group)
        interval_layout.setContentsMargins(0, 0, 0, 0)
        interval_layout.setSpacing(8)
        
        min_interval_label = QLabel("최소 간격(분):")
        min_interval_label.setStyleSheet("color: white;")
        self.min_interval = QSpinBox()
        self.min_interval.setRange(1, 1440)
        self.min_interval.setValue(5)
        self.min_interval.setStyleSheet("""
            QSpinBox {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #3d3d3d;
                padding: 5px;
                border-radius: 4px;
            }
        """)
        
        max_interval_label = QLabel("최대 간격(분):")
        max_interval_label.setStyleSheet("color: white;")
        self.max_interval = QSpinBox()
        self.max_interval.setRange(1, 1440)
        self.max_interval.setValue(15)
        self.max_interval.setStyleSheet(self.min_interval.styleSheet())
        
        # 반복 설정
        self.repeat_checkbox = QCheckBox("작업 반복")
        self.repeat_checkbox.setStyleSheet("""
            QCheckBox {
                color: white;
                spacing: 5px;
                padding: 5px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #5c85d6;
                background: transparent;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #5c85d6;
                background: #5c85d6;
                border-radius: 3px;
            }
        """)
        
        interval_layout.addWidget(min_interval_label)
        interval_layout.addWidget(self.min_interval)
        interval_layout.addWidget(max_interval_label)
        interval_layout.addWidget(self.max_interval)
        interval_layout.addSpacing(20)  # 간격 추가
        interval_layout.addWidget(self.repeat_checkbox)
        interval_layout.addStretch()

        # API Key 설정
        api_group = QWidget()
        api_layout = QHBoxLayout(api_group)
        api_layout.setContentsMargins(0, 0, 0, 0)
        
        api_label = QLabel("AI API Key:")
        api_label.setStyleSheet("color: white;")
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("API Key를 입력하세요")
        self.api_key_input.setStyleSheet("""
            QLineEdit {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #3d3d3d;
                padding: 5px;
                border-radius: 4px;
            }
        """)
        # API 키 입력값 변경 이벤트 연결
        self.api_key_input.textChanged.connect(self.on_api_key_changed)
        
        # API 키 검증 버튼 추가
        self.validate_api_btn = QPushButton("검증")
        self.validate_api_btn.setStyleSheet("""
            QPushButton {
                background-color: #5c85d6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #4a6fb8;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #aaaaaa;
            }
        """)
        self.validate_api_btn.clicked.connect(self.validate_api_key)
        
        # API 키 검증 상태 표시 레이블
        self.api_key_status = QLabel("")
        self.api_key_status.setStyleSheet("color: #808080; margin-left: 5px;")
        
        api_layout.addWidget(api_label)
        api_layout.addWidget(self.api_key_input, stretch=1)
        api_layout.addWidget(self.validate_api_btn)
        api_layout.addWidget(self.api_key_status)

        # 설정 영역에 위젯 추가
        settings_layout.addWidget(interval_group)
        settings_layout.addWidget(api_group)
        settings_group.setLayout(settings_layout)
        
        # 작업 관리 탭에 추가
        task_layout.addWidget(settings_group)
        task_manage_tab.setLayout(task_layout)
        
        # 2. 게시글 모니터 탭
        post_monitor_tab = QWidget()
        post_layout = QVBoxLayout()
        
        # BaseMonitorWidget에서 상속받은 task_monitor 직접 사용
        post_layout.addWidget(self.task_monitor)
        post_monitor_tab.setLayout(post_layout)
        
        # 3. 공지사항 탭
        notice_tab = QWidget()
        notice_layout = QVBoxLayout()
        notice_text = QTextEdit()
        notice_text.setReadOnly(True)
        notice_text.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: white;
                border: none;
            }
        """)
        notice_layout.addWidget(notice_text)
        notice_tab.setLayout(notice_layout)
        
        # 4. 기간연장/문의 탭
        support_tab = QWidget()
        support_layout = QVBoxLayout()
        
        contact_info = QLabel("""
            기간연장 및 문의사항은 아래로 연락주세요:
            
            카카오톡: @example
            이메일: support@example.com
            전화: 010-1234-5678
        """)
        contact_info.setStyleSheet("color: white; padding: 20px;")
        contact_info.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        support_layout.addWidget(contact_info)
        support_tab.setLayout(support_layout)
        
        # 탭 추가
        tab_widget.addTab(task_manage_tab, "작업 관리")
        tab_widget.addTab(post_monitor_tab, "작업 모니터")
        tab_widget.addTab(notice_tab, "공지사항")
        tab_widget.addTab(support_tab, "기간연장/문의")
        
        # 로그 모니터 - BaseMonitorWidget에서 상속받은 log_monitor 직접 사용
        self.log_monitor.setMinimumHeight(70)
        self.log_monitor.setMaximumHeight(120)
        
        # 로그 모니터 스타일 개선
        log_monitor_style = """
            QTableWidget {
                background-color: #2b2b2b;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                gridline-color: #3d3d3d;
            }
            QTableWidget::item {
                padding: 5px;
                border: none;
                min-height: 25px;
            }
            QHeaderView::section {
                background-color: #353535;
                padding: 5px;
                border: 1px solid #3d3d3d;
                color: white;
                font-weight: bold;
            }
            QTableCornerButton::section {
                background-color: #353535;
                border: 1px solid #3d3d3d;
            }
        """
        self.log_monitor.setStyleSheet(log_monitor_style)
        
        # 실행 버튼
        self.execute_btn = QPushButton("실행")
        self.execute_btn.setFixedHeight(40)  # 높이 고정
        self.execute_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.execute_btn.clicked.connect(self.toggle_execution)
        
        # 메인 레이아웃 구성
        layout.addWidget(tab_widget)
        layout.addWidget(next_task_info)
        layout.addWidget(self.log_monitor)
        layout.addWidget(self.execute_btn)
        self.setLayout(layout)

    def toggle_execution(self):
        """실행/중지 버튼 클릭 시 호출되는 메서드"""
        try:
            if not self.is_running:
                # 실행 시작 전 API 키 검증 확인
                api_key = self.api_key_input.text().strip()
                
                if not api_key:
                    QMessageBox.warning(self, "API 키 필요", "작업을 실행하기 전에 API 키를 입력해주세요.")
                    return
                    
                if not self.api_key_validated:
                    reply = QMessageBox.question(
                        self, 
                        "API 키 검증 필요", 
                        "API 키가 검증되지 않았습니다. 검증을 진행하시겠습니까?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes
                    )
                    
                    if reply == QMessageBox.Yes:
                        # API 키 검증 진행
                        self.validate_api_key()
                        # 검증 후에도 유효하지 않으면 실행 중단
                        if not self.api_key_validated:
                            return
                    else:
                        return
                
                # 작업 실행 버튼 클릭 로그 - 직접 콘솔에 출력하여 로그 재귀 호출 방지
                print("작업 실행 버튼이 클릭되었습니다.")
                print(f"작업 실행 상태 변경: is_running = {self.is_running} → True")
                
                # 실행 상태로 변경
                self.is_running = True
                self.execute_btn.setText("중지")
                self.execute_btn.setStyleSheet("""
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
                
                # 상태 변경 확인 로그 - 직접 콘솔에 출력
                print(f"버튼 상태 변경 후: is_running = {self.is_running}, 버튼 텍스트 = '중지'")
                
                # 실행 시그널 발생
                self.execute_tasks_clicked.emit(True)
                print("실행 시그널이 발생되었습니다.")
            else:
                # 작업 중지 버튼 클릭 로그 - 직접 콘솔에 출력
                print("작업 중지 버튼이 클릭되었습니다.")
                print(f"작업 실행 상태 변경: is_running = {self.is_running} → False")
                
                # 중지 상태로 변경
                self.is_running = False
                self.execute_btn.setText("실행")
                self.execute_btn.setStyleSheet("""
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
                
                # 상태 변경 확인 로그 - 직접 콘솔에 출력
                print(f"버튼 상태 변경 후: is_running = {self.is_running}, 버튼 텍스트 = '실행'")
                
                # 중지 시그널 발생
                self.execute_tasks_clicked.emit(False)
                print("중지 시그널이 발생되었습니다.")
        except Exception as e:
            # 예외 발생 시 콘솔에 출력
            print(f"toggle_execution 메서드 실행 중 오류 발생: {str(e)}")
            # 상태 초기화
            self.is_running = False
            self.execute_btn.setText("실행")
            self.execute_btn.setStyleSheet("""
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

    def show_monitor(self):
        self.log_monitor.setVisible(True)
        self.task_monitor.setVisible(True)

    def hide_monitor(self):
        self.log_monitor.setVisible(False)
        self.task_monitor.setVisible(False)

    def add_log_message(self, log_entry):
        """로그 메시지 추가 - RoutineMonitorWidget에 위임"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = log_entry.get('message', '')
        color = log_entry.get('color', 'black')
        
        # 로그 테이블에 새 행 추가
        row = self.log_monitor.rowCount()
        self.log_monitor.insertRow(row)
        
        # 시간 아이템 생성
        time_item = QTableWidgetItem(timestamp)
        time_item.setForeground(Qt.gray)
        
        # 메시지 아이템 생성
        message_item = QTableWidgetItem(message)
        if color == "red":
            message_item.setForeground(Qt.red)
        elif color == "blue":
            message_item.setForeground(Qt.blue)
        elif color == "green":
            message_item.setForeground(Qt.green)
        else:
            message_item.setForeground(Qt.white)
        
        # 아이템 설정
        self.log_monitor.setItem(row, 0, time_item)
        self.log_monitor.setItem(row, 1, message_item)
        
        # 새로 추가된 행으로 스크롤
        self.log_monitor.scrollToBottom()

    def on_task_selection_changed(self):
        """작업 선택 상태에 따라 삭제 버튼 활성화/비활성화"""
        self.remove_task_btn.setEnabled(bool(self.task_list.selectedItems()))

    def on_tasks_reordered(self):
        """작업 순서가 변경되었을 때 처리"""
        # 이 메서드는 작업 목록의 모델이 변경될 때 호출됩니다.
        # 여기에 필요한 처리를 추가할 수 있습니다.
        pass

    def on_api_key_changed(self):
        """API 키 입력값이 변경되었을 때 호출되는 메서드"""
        api_key = self.api_key_input.text().strip()
        
        # API 키가 변경되면 검증 상태 초기화
        self.api_key_validated = False
        self.api_key_status.setText("")
        
        # 메인 윈도우에 API 키 설정
        if hasattr(self.parent(), 'set_ai_api_key'):
            self.parent().set_ai_api_key(api_key)
        elif hasattr(self.parent().parent(), 'set_ai_api_key'):
            self.parent().parent().set_ai_api_key(api_key)
        
        # 검증 버튼 활성화/비활성화
        self.validate_api_btn.setEnabled(bool(api_key))
        
        # 로그 메시지 추가
        self.log.info("API 키가 변경되었습니다.")

    def validate_api_key(self):
        """API 키 검증 버튼 클릭 시 호출되는 메서드"""
        api_key = self.api_key_input.text().strip()
        
        if not api_key:
            QMessageBox.warning(self, "API 키 검증", "API 키를 입력해주세요.")
            return
        
        # 검증 중 UI 업데이트
        self.validate_api_btn.setEnabled(False)
        self.api_key_status.setText("검증 중...")
        self.api_key_status.setStyleSheet("color: #5c85d6;")
        
        # API 키 검증
        try:
            ai_generator = AIGenerator(api_key=api_key)
            is_valid, message = ai_generator.validate_api_key()
            
            if is_valid:
                self.api_key_validated = True
                self.api_key_status.setText("✓ 유효한 키")
                self.api_key_status.setStyleSheet("color: #4CAF50;")
                self.log.info("API 키 검증 성공: " + message)
            else:
                self.api_key_validated = False
                self.api_key_status.setText("✗ 유효하지 않음")
                self.api_key_status.setStyleSheet("color: #d65c5c;")
                self.log.error("API 키 검증 실패: " + message)
                QMessageBox.warning(self, "API 키 검증 실패", message)
        except Exception as e:
            self.api_key_validated = False
            self.api_key_status.setText("✗ 오류 발생")
            self.api_key_status.setStyleSheet("color: #d65c5c;")
            error_msg = f"API 키 검증 중 오류 발생: {str(e)}"
            self.log.error(error_msg)
            QMessageBox.critical(self, "API 키 검증 오류", error_msg)
        
        # 검증 완료 후 UI 업데이트
        self.validate_api_btn.setEnabled(True)

    def update_next_task_info(self, info):
        """다음 작업 정보 업데이트
        
        Args:
            info (dict): 다음 작업 정보
                - next_task_number (int): 다음 작업 번호
                - next_execution_time (str): 다음 실행 시간
                - wait_time (str): 대기 시간
        """
        next_task_number = info.get('next_task_number', 0)
        next_execution_time = info.get('next_execution_time', '')
        wait_time = info.get('wait_time', '')
        
        if next_task_number > 0:
            self.next_task_label.setText(
                f"다음 작업 #{next_task_number} - {next_execution_time} (대기: {wait_time})"
            )
        else:
            self.next_task_label.setText("대기 중...") 
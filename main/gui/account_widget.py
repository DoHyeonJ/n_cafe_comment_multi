from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QMessageBox, QListWidget,
                           QFileDialog, QDialog, QInputDialog, QProgressDialog)
from PyQt5.QtCore import pyqtSignal, QThread, Qt, QTimer
from ..api.auth import NaverAuth
import traceback
import pandas as pd
import os
import shutil
import time
import datetime
from PyQt5.QtWidgets import QApplication

class LoginWorker(QThread):
    finished = pyqtSignal(bool, dict)  # 성공 여부, 헤더 정보
    progress = pyqtSignal(str, str)  # 메시지, 색상

    def __init__(self, username, password):
        super().__init__()
        self.username = username
        self.password = password
        self.auth = NaverAuth()

    def run(self):
        try:
            self.progress.emit(f"계정 {self.username} 로그인 시도 중...", "blue")
            
            # 자격 증명 설정
            self.auth.set_credentials(self.username, self.password)
            
            # 로그인 시도
            success, headers = self.auth.login()
            
            if success:
                self.progress.emit(f"계정 {self.username} 로그인 성공!", "green")
                self.finished.emit(True, headers)
            else:
                self.progress.emit(f"계정 {self.username} 로그인 실패", "red")
                self.finished.emit(False, {})
        except Exception as e:
            self.progress.emit(f"로그인 오류: {str(e)}", "red")
            print(traceback.format_exc())
            self.finished.emit(False, {})

class AccountFileDialog(QDialog):
    """계정 파일 관리 다이얼로그"""
    file_selected = pyqtSignal(str)  # 파일 선택 시그널
    
    def __init__(self, account_dir, parent=None):
        super().__init__(parent)
        self.account_dir = account_dir
        self.selected_file = None
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("계정 파일 관리")
        self.setMinimumSize(500, 400)
        
        layout = QVBoxLayout()
        
        # 계정 파일 목록 레이블
        list_label = QLabel("저장된 계정 파일 목록")
        list_label.setStyleSheet("font-weight: bold; color: white;")
        layout.addWidget(list_label)
        
        # 계정 파일 목록
        self.file_list = QListWidget()
        self.file_list.setStyleSheet("""
            QListWidget {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #3d3d3d;
            }
            QListWidget::item:selected {
                background-color: #5c85d6;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #353535;
            }
        """)
        self.file_list.itemDoubleClicked.connect(self.on_item_selected)
        layout.addWidget(self.file_list)
        
        # 버튼 영역
        btn_layout = QHBoxLayout()
        
        # 새 파일 생성 버튼
        self.new_btn = QPushButton("새 파일 생성")
        self.new_btn.setStyleSheet("""
            QPushButton {
                background-color: #5c85d6;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4a6fb8;
            }
        """)
        self.new_btn.clicked.connect(self.create_new_file)
        
        # 파일 불러오기 버튼
        self.load_btn = QPushButton("불러오기")
        self.load_btn.setStyleSheet("""
            QPushButton {
                background-color: #5c85d6;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4a6fb8;
            }
        """)
        self.load_btn.clicked.connect(self.load_selected_file)
        
        # 파일 삭제 버튼
        self.delete_btn = QPushButton("삭제")
        self.delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #d65c5c;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #b84a4a;
            }
        """)
        self.delete_btn.clicked.connect(self.delete_selected_file)
        
        # 파일 이름 변경 버튼
        self.rename_btn = QPushButton("이름 변경")
        self.rename_btn.setStyleSheet("""
            QPushButton {
                background-color: #5c85d6;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #4a6fb8;
            }
        """)
        self.rename_btn.clicked.connect(self.rename_selected_file)
        
        btn_layout.addWidget(self.new_btn)
        btn_layout.addWidget(self.load_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addWidget(self.rename_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
        # 파일 목록 로드
        self.load_file_list()
        
    def load_file_list(self):
        """계정 파일 목록 로드"""
        self.file_list.clear()
        
        # account 폴더 내 엑셀 파일 목록 가져오기
        if os.path.exists(self.account_dir):
            files = [f for f in os.listdir(self.account_dir) if f.endswith('.xlsx') and not f.startswith('~$')]
            files.sort(key=lambda x: os.path.getmtime(os.path.join(self.account_dir, x)), reverse=True)
            
            for file in files:
                self.file_list.addItem(file)
                
        # 첫 번째 항목 선택
        if self.file_list.count() > 0:
            self.file_list.setCurrentRow(0)
            
    def on_item_selected(self, item):
        """항목 더블 클릭 시 호출"""
        self.selected_file = item.text()
        self.file_selected.emit(os.path.join(self.account_dir, self.selected_file))
        self.accept()
        
    def create_new_file(self):
        """새 계정 파일 생성"""
        # 현재 날짜와 시간으로 기본 파일명 생성
        default_name = f"계정목록_{self.get_current_date_time()}.xlsx"
        
        # 파일명 입력 다이얼로그
        file_name, ok = QInputDialog.getText(
            self, "새 계정 파일 생성", "파일 이름:", 
            QLineEdit.Normal, default_name
        )
        
        if ok and file_name:
            # 확장자 확인 및 추가
            if not file_name.endswith('.xlsx'):
                file_name += '.xlsx'
                
            # 파일 경로
            file_path = os.path.join(self.account_dir, file_name)
            
            # 이미 존재하는 파일인지 확인
            if os.path.exists(file_path):
                reply = QMessageBox.question(
                    self, '파일 덮어쓰기',
                    f'"{file_name}" 파일이 이미 존재합니다. 덮어쓰시겠습니까?',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return
            
            try:
                # 템플릿 생성
                df = pd.DataFrame(columns=['아이디', '비밀번호'])
                # 예시 데이터 추가
                df.loc[0] = ['example_id', 'example_password']
                # 저장
                df.to_excel(file_path, index=False)
                
                # 파일 목록 갱신
                self.load_file_list()
                
                # 새로 생성한 파일 선택
                items = self.file_list.findItems(file_name, Qt.MatchExactly)
                if items:
                    self.file_list.setCurrentItem(items[0])
                    
                QMessageBox.information(self, "파일 생성 완료", f"새 계정 파일이 생성되었습니다:\n{file_name}")
            except Exception as e:
                QMessageBox.critical(self, "오류", f"파일 생성 중 오류가 발생했습니다:\n{str(e)}")
                
    def load_selected_file(self):
        """선택한 파일 불러오기"""
        if not self.file_list.currentItem():
            QMessageBox.warning(self, "경고", "불러올 파일을 선택해주세요.")
            return
            
        self.selected_file = self.file_list.currentItem().text()
        self.file_selected.emit(os.path.join(self.account_dir, self.selected_file))
        self.accept()
        
    def delete_selected_file(self):
        """선택한 파일 삭제"""
        if not self.file_list.currentItem():
            QMessageBox.warning(self, "경고", "삭제할 파일을 선택해주세요.")
            return
            
        file_name = self.file_list.currentItem().text()
        file_path = os.path.join(self.account_dir, file_name)
        
        reply = QMessageBox.question(
            self, '파일 삭제 확인',
            f'"{file_name}" 파일을 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                os.remove(file_path)
                self.load_file_list()
                QMessageBox.information(self, "삭제 완료", f"파일이 삭제되었습니다:\n{file_name}")
            except Exception as e:
                QMessageBox.critical(self, "오류", f"파일 삭제 중 오류가 발생했습니다:\n{str(e)}")
                
    def rename_selected_file(self):
        """선택한 파일 이름 변경"""
        if not self.file_list.currentItem():
            QMessageBox.warning(self, "경고", "이름을 변경할 파일을 선택해주세요.")
            return
            
        old_name = self.file_list.currentItem().text()
        old_path = os.path.join(self.account_dir, old_name)
        
        # 확장자 제외한 파일명
        name_without_ext = os.path.splitext(old_name)[0]
        
        # 새 이름 입력 다이얼로그
        new_name, ok = QInputDialog.getText(
            self, "파일 이름 변경", "새 파일 이름:", 
            QLineEdit.Normal, name_without_ext
        )
        
        if ok and new_name:
            # 확장자 추가
            if not new_name.endswith('.xlsx'):
                new_name += '.xlsx'
                
            # 새 파일 경로
            new_path = os.path.join(self.account_dir, new_name)
            
            # 이미 존재하는 파일인지 확인
            if os.path.exists(new_path) and old_name != new_name:
                reply = QMessageBox.question(
                    self, '파일 덮어쓰기',
                    f'"{new_name}" 파일이 이미 존재합니다. 덮어쓰시겠습니까?',
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return
            
            try:
                # 파일 이름 변경
                os.rename(old_path, new_path)
                
                # 파일 목록 갱신
                self.load_file_list()
                
                # 이름 변경된 파일 선택
                items = self.file_list.findItems(new_name, Qt.MatchExactly)
                if items:
                    self.file_list.setCurrentItem(items[0])
                    
                QMessageBox.information(self, "이름 변경 완료", f"파일 이름이 변경되었습니다:\n{old_name} → {new_name}")
            except Exception as e:
                QMessageBox.critical(self, "오류", f"파일 이름 변경 중 오류가 발생했습니다:\n{str(e)}")
                
    def get_current_date_time(self):
        """현재 날짜와 시간을 문자열로 반환"""
        now = datetime.datetime.now()
        return now.strftime("%Y%m%d_%H%M%S")

class AccountWidget(QWidget):
    login_success = pyqtSignal(dict)  # 로그인 성공 시그널 (헤더 정보 전달)
    account_added = pyqtSignal(str, str)  # 계정 추가 시그널 (id, pw)
    account_removed = pyqtSignal(str)  # 계정 삭제 시그널 (id)
    account_selected = pyqtSignal(str)  # 계정 선택 시그널 (id)
    
    def __init__(self, log, monitor_widget):
        super().__init__()
        self.log = log
        self.monitor_widget = monitor_widget
        self.account_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "account")
        self.template_path = os.path.join(self.account_dir, "account_template.xlsx")
        self.login_workers = []  # 로그인 워커 목록 관리
        self.verified_accounts = set()  # 검증된 계정 목록
        self.account_passwords = {}  # 계정 비밀번호 저장 딕셔너리
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 계정 목록
        self.account_list = QListWidget()
        self.account_list.itemClicked.connect(self.on_account_selected)  # 계정 선택 이벤트 연결
        self.account_list.setStyleSheet("""
            QListWidget {
                background-color: #2b2b2b;
                border: 1px solid #3d3d3d;
                padding: 5px;
            }
            QListWidget::item {
                color: #cccccc;
                padding: 5px 8px;
                margin: 1px;
                border-radius: 3px;
                min-height: 20px;
                font-size: 12px;
            }
            QListWidget::item:selected {
                background-color: #5c85d6;
                color: white;
                font-weight: bold;
            }
            QListWidget::item:hover:!selected {
                background-color: #353535;
            }
        """)
        
        # 계정 목록 크기 설정
        self.account_list.setMinimumHeight(100)
        self.account_list.setMaximumHeight(150)
        
        # 버튼 영역 (하단에 배치)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)  # 버튼 간격 설정
        
        # 계정 설정 관리 버튼
        self.account_manage_btn = QPushButton("계정 그룹 관리")
        self.account_manage_btn.setStyleSheet("""
            QPushButton {
                background-color: #5c85d6;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #4a6fb8;
            }
        """)
        self.account_manage_btn.clicked.connect(self.show_account_file_dialog)

        # 계정 검증 버튼
        self.verify_btn = QPushButton("선택 계정 검증")
        self.verify_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.verify_btn.clicked.connect(self.verify_selected_account)
        self.verify_btn.setEnabled(False)  # 초기에는 비활성화

        # 일괄 검증 버튼
        self.verify_all_btn = QPushButton("일괄 검증")
        self.verify_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #FFA500;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #FF8C00;
            }
        """)
        self.verify_all_btn.clicked.connect(self.verify_all_accounts)
        self.verify_all_btn.setEnabled(False)  # 초기에는 비활성화
        
        btn_layout.addWidget(self.account_manage_btn)
        btn_layout.addWidget(self.verify_btn)
        btn_layout.addWidget(self.verify_all_btn)
        
        # 레이아웃 구성
        layout.addWidget(self.account_list)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        
        # 템플릿 파일이 없으면 생성
        self.create_template_if_not_exists()
        
    def create_template_if_not_exists(self):
        """엑셀 템플릿 파일이 없으면 생성"""
        if not os.path.exists(self.template_path):
            # 템플릿 생성
            df = pd.DataFrame(columns=['아이디', '비밀번호'])
            # 예시 데이터 추가
            df.loc[0] = ['example_id', 'example_password']
            # 저장
            df.to_excel(self.template_path, index=False)
            self.log.info(f"계정 템플릿 파일이 생성되었습니다: {self.template_path}")
    
    def show_account_file_dialog(self):
        """계정 파일 관리 다이얼로그 표시"""
        dialog = AccountFileDialog(self.account_dir, self)
        dialog.file_selected.connect(self.load_excel_file)
        dialog.setStyleSheet("""
            QDialog {
                background-color: #1e1e1e;
                color: white;
            }
            QLabel {
                color: white;
            }
        """)
        dialog.exec_()
    
    def load_excel_file(self, file_path):
        """선택한 엑셀 파일 불러오기"""
        try:
            self.load_excel(file_path)
        except Exception as e:
            self.log.error(f"엑셀 파일 불러오기 중 오류 발생: {str(e)}")
            QMessageBox.critical(self, "오류", f"엑셀 파일 불러오기 중 오류가 발생했습니다.\n{str(e)}")
    
    def load_excel(self, file_path):
        """엑셀 파일에서 계정 정보 불러오기"""
        try:
            # 엑셀 파일 읽기
            df = pd.read_excel(file_path)
            
            # 필수 열 확인
            required_columns = ['아이디', '비밀번호']
            if not all(col in df.columns for col in required_columns):
                QMessageBox.warning(self, "형식 오류", "엑셀 파일에 '아이디'와 '비밀번호' 열이 모두 포함되어 있어야 합니다.")
                return
            
            # 계정 목록 초기화
            self.account_list.clear()
            self.verified_accounts.clear()  # 검증된 계정 목록 초기화
            
            # 기존 로그인 워커 정리
            for worker in self.login_workers:
                if worker.isRunning():
                    worker.terminate()
                    worker.wait()
            self.login_workers.clear()
            
            # 유효한 계정 정보 추출
            valid_accounts = []
            for _, row in df.iterrows():
                username = str(row['아이디']).strip()
                password = str(row['비밀번호']).strip()
                
                if not username or not password or username == 'nan' or password == 'nan':
                    continue
                
                valid_accounts.append((username, password))
            
            if not valid_accounts:
                QMessageBox.warning(self, "계정 없음", "엑셀 파일에 유효한 계정 정보가 없습니다.")
                return
            
            # 계정 정보 저장 (비밀번호 포함)
            self.account_passwords = {}  # 계정 비밀번호 저장 딕셔너리
            
            # 모든 계정을 리스트에 추가
            for username, password in valid_accounts:
                # 계정이 이미 목록에 있는지 확인
                items = self.account_list.findItems(username, Qt.MatchExactly)
                if not items:  # 중복되지 않은 경우에만 추가
                    self.account_list.addItem(username)
                    self.account_added.emit(username, password)
                    # 비밀번호 저장
                    self.account_passwords[username] = password
            
            # 첫 번째 계정 선택 및 자동 로그인
            if self.account_list.count() > 0:
                self.account_list.setCurrentRow(0)
                first_username = self.account_list.item(0).text()
                self.account_selected.emit(first_username)
                
                # 첫 번째 계정 자동 로그인
                first_username, first_password = valid_accounts[0]
                self.log.info(f"첫 번째 계정 '{first_username}'으로 로그인을 시도합니다.")
                self.start_login(first_username, first_password)
            
            # 버튼 활성화
            self.verify_all_btn.setEnabled(self.account_list.count() > 0)
            
            # 결과 메시지
            file_name = os.path.basename(file_path)
            self.log.info(f"계정 파일 '{file_name}'에서 {len(valid_accounts)}개의 계정을 불러왔습니다.")
            
        except Exception as e:
            self.log.error(f"엑셀 파일 불러오기 중 오류 발생: {str(e)}")
            QMessageBox.critical(self, "오류", f"엑셀 파일 불러오기 중 오류가 발생했습니다.\n{str(e)}")
    
    def start_login(self, username, password):
        """계정 로그인 시작"""
        # 로그인 워커 생성
        worker = LoginWorker(username, password)
        worker.progress.connect(self.on_login_progress)
        worker.finished.connect(lambda success, headers: self.on_login_finished(success, headers, username, password))
        
        # 워커 목록에 추가하고 시작
        self.login_workers.append(worker)
        worker.start()
        
    def on_login_progress(self, message, color):
        """로그인 진행상황 업데이트"""
        self.log.add_log(message, color)
        self.monitor_widget.add_log_message({'message': message, 'color': color})
        
    def on_login_finished(self, success, headers, username, password):
        """로그인 완료 처리"""
        if success:
            # 검증된 계정 목록에 추가
            self.verified_accounts.add(username)
            
            # 비밀번호 저장
            self.account_passwords[username] = password
            
            # 계정 목록에 추가 또는 업데이트
            # 정확한 계정 ID 검색을 위해 MatchExactly 사용
            items = self.account_list.findItems(username, Qt.MatchExactly)
            
            # 체크 마크가 있는 경우를 위해 StartsWith로도 검색
            if not items:
                items = self.account_list.findItems(username + " ", Qt.MatchStartsWith)
            
            if items:
                # 기존 항목 업데이트
                self.update_account_item_style(items[0])
            else:
                # 새 항목 추가 (이 부분은 일반적으로 실행되지 않아야 함)
                self.log.warning(f"계정 '{username}'이 목록에 없어 새로 추가합니다.")
                new_item = QListWidgetItem(username)
                self.account_list.addItem(new_item)
                self.update_account_item_style(new_item)
            
            # 계정 추가 시그널 발생
            self.account_added.emit(username, password)
            
            # 로그인 성공 시그널 발생
            self.login_success.emit(headers)
            
            # 현재 선택된 계정이 로그인된 계정인 경우 선택 시그널 다시 발생
            if self.account_list.currentItem():
                current_account = self.account_list.currentItem().text().split(' ')[0]
                if current_account == username:
                    self.account_selected.emit(username)
            
            self.log.info(f"계정 {username} 검증 완료")
        else:
            self.log.error(f"계정 {username} 로그인 검증 실패")
            
            # 실패한 계정 스타일 업데이트
            # 정확한 계정 ID 검색을 위해 MatchExactly 사용
            items = self.account_list.findItems(username, Qt.MatchExactly)
            
            # 체크 마크가 있는 경우를 위해 StartsWith로도 검색
            if not items:
                items = self.account_list.findItems(username + " ", Qt.MatchStartsWith)
                
            if items:
                items[0].setForeground(Qt.red)
                items[0].setText(f"{username} ✗")  # 실패 표시 추가

    def on_account_selected(self, item):
        """계정 선택 시 호출"""
        # 계정 ID에서 ✓ 또는 ✗ 마크 제거
        account_id = item.text().split(' ')[0]
        
        # 계정 선택 시그널 발생
        self.account_selected.emit(account_id)
        
        # 검증 버튼 활성화
        self.verify_btn.setEnabled(True)
        
        # 계정 상태에 따라 아이템 스타일 업데이트
        self.update_account_item_style(item)

    def verify_selected_account(self):
        """선택된 계정 검증"""
        if not self.account_list.currentItem():
            return
            
        account_id = self.account_list.currentItem().text().split(' ')[0]  # ✓ 또는 ✗ 마크 제거
        
        # 계정 비밀번호 가져오기
        password = None
        
        # 내부 저장된 비밀번호 확인
        if account_id in self.account_passwords:
            password = self.account_passwords[account_id]
        else:
            # MainWindow에서 비밀번호 가져오기
            main_window = self.parent()
            if hasattr(main_window, 'accounts') and account_id in main_window.accounts:
                password = main_window.accounts[account_id]['pw']
        
        if password:
            self.log.info(f"계정 '{account_id}'의 로그인을 시도합니다.")
            self.start_login(account_id, password)
        else:
            self.log.error(f"계정 '{account_id}'의 비밀번호를 찾을 수 없습니다.")

    def verify_all_accounts(self):
        """모든 계정 일괄 검증"""
        if self.account_list.count() == 0:
            return
            
        reply = QMessageBox.question(
            self,
            '일괄 검증 확인',
            f'모든 계정({self.account_list.count()}개)의 로그인을 순차적으로 검증하시겠습니까?\n이 작업은 시간이 걸릴 수 있습니다.',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # 진행 상태 대화상자 생성
            self.progress_dialog = QProgressDialog("계정 검증 중...", "취소", 0, self.account_list.count(), self)
            self.progress_dialog.setWindowTitle("계정 일괄 검증")
            self.progress_dialog.setWindowModality(Qt.WindowModal)
            self.progress_dialog.setAutoClose(True)
            self.progress_dialog.setAutoReset(True)
            self.progress_dialog.setCancelButton(None)  # 취소 버튼 비활성화
            self.progress_dialog.setMinimumDuration(0)
            self.progress_dialog.show()
            
            # MainWindow 참조 가져오기
            self.main_window = self.parent()
            
            # 검증할 계정 목록 생성
            self.accounts_to_verify = []
            for i in range(self.account_list.count()):
                account_id = self.account_list.item(i).text().split(' ')[0]  # ✓ 또는 ✗ 마크 제거
                # 이미 검증된 계정은 건너뛰기
                if account_id not in self.verified_accounts:
                    self.accounts_to_verify.append(account_id)
            
            # 현재 진행 중인 계정 인덱스
            self.current_verify_index = 0
            
            # 첫 번째 계정 검증 시작
            self.verify_next_account()
    
    def verify_next_account(self):
        """다음 계정 검증"""
        # 모든 계정 검증 완료 확인
        if self.current_verify_index >= len(self.accounts_to_verify):
            self.progress_dialog.setValue(self.account_list.count())
            self.log.info(f"모든 계정 검증이 완료되었습니다.")
            return
        
        # 현재 계정 가져오기
        account_id = self.accounts_to_verify[self.current_verify_index]
        
        # 진행 상태 업데이트
        self.progress_dialog.setValue(self.current_verify_index)
        self.progress_dialog.setLabelText(f"계정 검증 중: {account_id} ({self.current_verify_index + 1}/{len(self.accounts_to_verify)})")
        
        # TODO: USB 테더링을 통한 IP 변경 기능 추가
        # 각 계정 로그인 전에 IP를 변경하여 보안 강화
        # change_ip_via_usb_tethering()
        
        # 계정 비밀번호 가져오기
        password = None
        if account_id in self.account_passwords:
            password = self.account_passwords[account_id]
        else:
            if hasattr(self.main_window, 'accounts') and account_id in self.main_window.accounts:
                password = self.main_window.accounts[account_id]['pw']
        
        if password:
            self.log.info(f"계정 '{account_id}'의 로그인을 시도합니다.")
            
            # 로그인 워커 생성 및 시그널 연결
            worker = LoginWorker(account_id, password)
            worker.progress.connect(self.on_login_progress)
            
            # 로그인 완료 시 다음 계정 검증으로 넘어가는 콜백 추가
            worker.finished.connect(lambda success, headers: self.on_verify_login_finished(success, headers, account_id, password))
            
            # 워커 목록에 추가하고 시작
            self.login_workers.append(worker)
            worker.start()
        else:
            self.log.error(f"계정 '{account_id}'의 비밀번호를 찾을 수 없습니다.")
            # 다음 계정으로 진행
            self.current_verify_index += 1
            QTimer.singleShot(500, self.verify_next_account)
    
    def on_verify_login_finished(self, success, headers, username, password):
        """일괄 검증 시 로그인 완료 처리"""
        # 기존 로그인 완료 처리 호출
        self.on_login_finished(success, headers, username, password)
        
        # 다음 계정으로 진행
        self.current_verify_index += 1
        
        # 약간의 지연 후 다음 계정 검증 (UI 업데이트 및 네트워크 부하 방지)
        QTimer.singleShot(2000, self.verify_next_account)

    def update_account_item_style(self, item):
        """계정 아이템의 스타일 업데이트"""
        account_id = item.text().split(' ')[0]  # ✓ 또는 ✗ 마크 제거
        if account_id in self.verified_accounts:
            # 검증된 계정 스타일
            item.setForeground(Qt.green)
            item.setText(f"{account_id} ✓")  # 체크 표시 추가
        else:
            # 미검증 계정 스타일
            item.setForeground(Qt.white)
            item.setText(account_id)  # 원래 텍스트로 복원 
import sys
import os
from PyQt5.QtWidgets import QApplication
from main.gui import MainWindow

def get_app_dir():
    """애플리케이션 디렉토리 경로 반환"""
    if getattr(sys, 'frozen', False):
        # PyInstaller로 빌드된 경우
        return os.path.dirname(sys.executable)
    else:
        # 일반 Python 스크립트로 실행된 경우
        return os.path.dirname(os.path.abspath(__file__))

def main():
    """애플리케이션의 메인 진입점"""
    app = QApplication(sys.argv)
    
    # 애플리케이션 기본 디렉토리 생성 (프로그램 실행 폴더 내)
    app_dir = get_app_dir()
    # settings_dir = os.path.join(app_dir, "settings")
    # os.makedirs(settings_dir, exist_ok=True)
    
    # 계정 관리를 위한 account 폴더 생성
    account_dir = os.path.join(app_dir, "account")
    os.makedirs(account_dir, exist_ok=True)
    
    # 메인 윈도우 생성 및 표시
    window = MainWindow()
    window.show()
    
    # 애플리케이션 실행
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 
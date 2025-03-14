from main.api.auth import NaverAuth
from main.api.ai_generator import AIGenerator
from main.api.image import ImageAPI
from main.api.cafe import CafeAPI
from main.utils.log import Log
from main.api.reply import ReplyAPI
from main.utils.openai_utils import OpenAIGenerator
import traceback
import os
import random
from PyQt5.QtCore import QThread, pyqtSignal, QMetaObject, Qt, Q_ARG, QVariant
import time

# 작업관리에서 작업 리스트를 가져오고 작업에 맞는 설정값들은 스케줄러를 만들고 별도로 관리한다.

class Worker(QThread):
    # 시그널 정의
    task_started = pyqtSignal(dict)  # 작업 시작 시그널
    task_completed = pyqtSignal(dict)  # 작업 완료 시그널
    task_error = pyqtSignal(dict, str)  # 작업 오류 시그널
    log_message = pyqtSignal(dict)  # 로그 메시지 시그널
    post_completed = pyqtSignal(dict)  # 게시글 등록 완료 시그널 (추가)
    next_task_info = pyqtSignal(dict)  # 다음 작업 정보 시그널 (추가)
    all_tasks_completed = pyqtSignal(bool)  # 모든 작업 완료 시그널 (추가) - bool 파라미터는 정상 완료 여부
    
    def __init__(self, main_window=None):
        super().__init__()
        self.tasks = []
        self.is_running = False
        self.main_window = main_window
        self.min_interval = 5  # 기본값 5분
        self.max_interval = 15  # 기본값 15분
        self.logger = Log()  # Log 클래스 인스턴스 생성
        
    def set_tasks(self, tasks):
        """작업 리스트 설정
        
        Args:
            tasks (list): 실행할 작업 리스트
        """
        self.tasks = tasks
        
    def set_main_window(self, main_window):
        """메인 윈도우 설정
        
        Args:
            main_window: MainWindow 인스턴스
        """
        self.main_window = main_window
        
    def stop(self):
        """작업 실행 중지"""
        if self.is_running:
            self.add_log_message({
                'message': "[작업 중지 요청] 작업 중지가 요청되었습니다.",
                'color': 'yellow'
            })
            self.is_running = False
            self.add_log_message({
                'message': "[작업 중지 처리] is_running 상태가 False로 변경되었습니다.",
                'color': 'yellow'
            })
            self.wait()  # 스레드가 종료될 때까지 대기

    def add_log_message(self, message_data):
        """로그 메시지 추가 및 시그널 발생
        
        Args:
            message_data (dict): 로그 메시지 데이터
                - message (str): 로그 메시지
                - color (str, optional): 메시지 색상 (기본값: 'black')
        """
        try:
            # 로그 메시지 시그널 발생
            self.log_message.emit(message_data)
            
            # 로그 출력 (디버깅용)
            message = message_data.get('message', '')
            color = message_data.get('color', 'black')
            
            # 콘솔에 로그 출력
            print(f"[Worker] {message}")
            
            # 파일에 로그 기록 (예외 처리)
            try:
                if color == "red":
                    self.logger.error(message)
                elif color == "yellow":
                    self.logger.warning(message)
                elif color == "blue":
                    self.logger.info(message)
                elif color == "green":
                    self.logger.info(message)
                else:
                    self.logger.info(message)
            except Exception as log_error:
                print(f"로그 파일 기록 중 오류 발생: {str(log_error)}")
                
        except Exception as e:
            # 로그 추가 중 오류 발생 시 콘솔에만 출력
            print(f"로그 추가 중 오류 발생: {str(e)}")
        
        # 메인 윈도우 직접 접근 방식은 제거 (스레드 안전을 위해 시그널만 사용)

    def set_intervals(self, min_interval, max_interval):
        """작업 간 대기 시간 간격 설정
        
        Args:
            min_interval (int): 최소 대기 시간 (분)
            max_interval (int): 최대 대기 시간 (분)
        """
        self.min_interval = min_interval
        self.max_interval = max_interval

    def get_random_wait_time(self):
        """최소/최대 간격 사이의 랜덤한 대기 시간(초) 반환"""
        min_seconds = self.min_interval * 60
        max_seconds = self.max_interval * 60
        return random.randint(min_seconds, max_seconds)

    def format_time_remaining(self, seconds):
        """남은 시간을 분:초 형식으로 변환"""
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}분 {seconds}초"

    def get_next_execution_time(self, wait_seconds):
        """다음 실행 시간을 계산"""
        from datetime import datetime, timedelta
        next_time = datetime.now() + timedelta(seconds=wait_seconds)
        return next_time.strftime("%H:%M:%S")

    def run(self):
        """작업 실행 (QThread에서 오버라이드)"""
        self.is_running = True
        
        try:
            # 작업 리스트가 비어있는지 확인
            if not self.tasks:
                self.add_log_message({
                    'message': "실행할 작업이 없습니다. 작업 실행이 중지됩니다.",
                    'color': 'red'
                })
                # 작업이 없는 경우도 완료 시그널 발생 (정상 완료)
                self.all_tasks_completed.emit(True)
                self.is_running = False
                return
            
            # 작업 반복 설정 확인
            repeat_tasks = False
            

        except Exception as e:
            # 예외 발생 시 로그 추가 및 작업 중지
            error_msg = f"작업 실행 중 오류 발생: {traceback.format_exc()}"
            print(error_msg)  # 콘솔에 출력
            
            try:
                self.add_log_message({
                    'message': error_msg,
                    'color': 'red'
                })
            except:
                print("로그 메시지 추가 중 추가 오류 발생")
                
            self.is_running = False
            self.all_tasks_completed.emit(False)
        
        finally:
            # 작업 종료 처리
            self.is_running = False

    def get_account_header_info(self, account_id):
        """계정 헤더 정보 가져오기
        
        Args:
            account_id (str): 계정 ID
            
        Returns:
            dict: 계정 헤더 정보
        """
        # 메인 윈도우 객체 확인
        if not self.main_window:
            raise ValueError("MainWindow 인스턴스가 설정되지 않았습니다.")
            
        # 계정 정보 확인
        if account_id not in self.main_window.accounts:
            raise ValueError(f"계정 '{account_id}'를 찾을 수 없습니다.")
            
        # 헤더 정보 가져오기
        headers = self.main_window.accounts[account_id].get('headers', {})
        
        # 헤더 유효성 검사 (12시간 이내인지)
        if not self.main_window.is_header_valid(headers):
            # 헤더가 유효하지 않은 경우 (12시간 초과)
            # 로그 메시지 추가
            self.add_log_message({
                'message': f"계정 '{account_id}'의 헤더 정보가 만료되었습니다. 재로그인이 필요합니다.",
                'color': 'red'
            })
            
            # 계정 비밀번호 가져오기
            password = self.main_window.accounts[account_id].get('pw', '')
            if not password:
                raise ValueError(f"계정 '{account_id}'의 비밀번호 정보가 없습니다.")
                
            # 재로그인 시도
            self.add_log_message({
                'message': f"계정 '{account_id}' 재로그인 시도 중...",
                'color': 'blue'
            })
            
            # NaverAuth 인스턴스 생성 및 로그인
            auth = NaverAuth()
            auth.set_credentials(account_id, password)
            success = auth.login()
            
            if success:
                # 로그인 성공 시 헤더 정보 업데이트
                headers = auth.get_headers()
                self.main_window.accounts[account_id]['headers'] = headers
                
                self.add_log_message({
                    'message': f"계정 '{account_id}' 재로그인 성공!",
                    'color': 'green'
                })
            else:
                # 로그인 실패
                self.add_log_message({
                    'message': f"계정 '{account_id}' 재로그인 실패",
                    'color': 'red'
                })
                raise ValueError(f"계정 '{account_id}' 재로그인에 실패했습니다.")
        
        # 기본 헤더 설정
        default_headers = {
            "origin": "https://cafe.naver.com",
            "referer": "https://cafe.naver.com",
            "x-cafe-product": "pc",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }
        
        # 헤더 병합 (기본 헤더 + 계정 헤더)
        merged_headers = default_headers.copy()
        for key, value in headers.items():
            if not key.startswith('_'):  # 내부 사용 필드는 제외
                if isinstance(value, (str, bytes)):
                    merged_headers[key] = value
                else:
                    merged_headers[key] = str(value)

        # 로그 메시지 추가
        self.add_log_message({
            'message': f"계정 '{account_id}'의 헤더 정보를 성공적으로 가져왔습니다.",
            'color': 'green'
        })
            
        return merged_headers

    def get_cafe_and_board_info(self, cafe_settings):
        """카페 및 게시판 정보 가져오기
        
        Args:
            cafe_settings (dict): 카페 설정 정보
            
        Returns:
            dict: 카페 및 게시판 정보
        """
        # 필수 정보 확인
        if not cafe_settings:
            raise ValueError("카페 설정 정보가 없습니다.")
            
        # 필수 필드 확인
        required_fields = ['cafe_name', 'cafe_id', 'board_name', 'board_id']
        for field in required_fields:
            if field not in cafe_settings:
                raise ValueError(f"카페 설정에 필수 필드 '{field}'가 없습니다.")
        
        # 카페 및 게시판 정보 구성
        cafe_info = {
            'cafe_id': cafe_settings['cafe_id'],
            'cafe_name': cafe_settings['cafe_name'],
            'cafe_url': cafe_settings.get('cafe_url', cafe_settings['cafe_name']),  # cafe_url이 없으면 cafe_name을 사용
            'board_id': cafe_settings['board_id'],
            'board_name': cafe_settings['board_name'],
        }
        
        # 추가 설정이 있으면 포함
        for key, value in cafe_settings.items():
            if key not in cafe_info:
                cafe_info[key] = value
                
        # 로그 메시지 추가
        self.add_log_message({
            'message': f"카페 정보 로드: {cafe_info['cafe_name']} - {cafe_info['board_name']}",
            'color': 'blue'
        })
        
        return cafe_info
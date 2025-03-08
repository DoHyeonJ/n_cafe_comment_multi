from main.api.auth import NaverAuth
from main.api.ai_generator import AIGenerator
from main.api.post import PostAPI
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
import requests
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
            if self.main_window and hasattr(self.main_window, 'monitor_widget'):
                repeat_tasks = self.main_window.monitor_widget.repeat_checkbox.isChecked()
                
                if repeat_tasks:
                    self.add_log_message({
                        'message': "작업 반복 모드가 활성화되었습니다. 모든 작업 완료 후 처음부터 다시 시작합니다.",
                        'color': 'blue'
                    })
                else:
                    self.add_log_message({
                        'message': "작업 반복 모드가 비활성화되었습니다. 모든 작업 완료 후 종료됩니다.",
                        'color': 'blue'
                    })
            
            # 계정별 헤더 정보 캐시
            account_headers = {}
            
            # 작업 순차적으로 실행
            for i, task in enumerate(self.tasks):
                # 실행 상태 확인
                if not self.is_running:
                    self.add_log_message({
                        'message': "작업이 중지되었습니다.",
                        'color': 'yellow'
                    })
                    # 작업이 중간에 중지된 경우 시그널 발생 (비정상 완료)
                    self.all_tasks_completed.emit(False)
                    return
                
                try:
                    # 작업 상태 업데이트
                    task['status'] = 'running'
                    # 작업 시작 시그널 발생
                    self.task_started.emit(task)
                    
                    # 01. 작업에 해당하는 계정 헤더 정보를 가져온다.
                    account_id = task['account_id']
                    
                    # 캐시된 헤더 정보가 없거나 만료된 경우 새로 가져오기
                    if account_id not in account_headers or not self.main_window.is_header_valid(account_headers[account_id]):
                        headers = self.get_account_header_info(account_id)
                        account_headers[account_id] = headers
                    else:
                        headers = account_headers[account_id]
                    
                    self.add_log_message({
                        'message': f"계정 '{account_id}'로 작업을 시작합니다.",
                        'color': 'blue'
                    })

                    # 02. 선택된 카페와 게시판 정보를 가져온다.
                    cafe_info = self.get_cafe_and_board_info(task['settings']['cafe'])

                    # 03. AI 프롬프트를 통해 제목, 내용을 생성한다.
                    title, content = self.generate_title_and_content(task['settings']['content'], task['settings']['cafe'], account_id)

                    # 04. 생성된 제목과 내용을 통해 게시글을 작성한다.
                    post_url = self.write_post(headers, cafe_info, title, content, task['settings'].get('reply'))
                    
                    # 05. 작업 상태 업데이트
                    task['status'] = 'completed'
                    task['post_url'] = post_url
                    
                    # 06. 작업 완료 후 닉네임 변경
                    if cafe_info.get('use_nickname', False):
                        self.add_log_message({
                            'message': "게시글 작성 완료 후 닉네임 변경을 시도합니다.",
                            'color': 'blue'
                        })
                        self.change_nickname_after_post(headers, cafe_info['cafe_id']['id'])
                    
                    # 작업 완료 시그널 발생
                    self.task_completed.emit(task)
                    
                    # 다음 작업이 있는 경우 대기 시간 계산 및 알림
                    if i < len(self.tasks) - 1 and self.is_running:
                        wait_seconds = self.get_random_wait_time()
                        next_time = self.get_next_execution_time(wait_seconds)
                        time_remaining = self.format_time_remaining(wait_seconds)
                        
                        # 실행 상태 확인 로그
                        self.add_log_message({
                            'message': f"[상태 확인] is_running: {self.is_running}",
                            'color': 'blue'
                        })
                        
                        # 다음 작업 정보 로그
                        next_task = self.tasks[i + 1]
                        self.add_log_message({
                            'message': f"다음 작업은 계정 '{next_task['account_id']}'의 작업입니다.",
                            'color': 'blue'
                        })
                        
                        # 대기 시작 로그
                        self.add_log_message({
                            'message': f"[대기 시작] 다음 작업까지 {time_remaining} 대기 (총 {wait_seconds}초)",
                            'color': 'blue'
                        })
                        
                        # 다음 작업 정보 시그널 발생
                        next_task_info = {
                            'next_task_number': i + 2,  # 1-based index
                            'next_execution_time': next_time,
                            'wait_time': time_remaining
                        }
                        self.next_task_info.emit(next_task_info)
                        
                        # 로그 메시지 추가
                        self.add_log_message({
                            'message': f"다음 작업 #{i+2}는 {next_time}에 실행됩니다. (대기 시간: {time_remaining})",
                            'color': 'blue'
                        })
                        
                        # 대기 시작
                        remaining_seconds = wait_seconds
                        
                        # 대기 루프 시작 - is_running 상태를 지속적으로 확인
                        self.add_log_message({
                            'message': f"[대기 루프 시작] 대기 중 is_running 상태를 지속적으로 확인합니다.",
                            'color': 'blue'
                        })
                        
                        # 이전 is_running 상태 저장
                        prev_is_running = self.is_running
                        
                        while remaining_seconds > 0 and self.is_running:
                            # is_running 상태가 변경되었는지 확인
                            if prev_is_running != self.is_running:
                                self.add_log_message({
                                    'message': f"[상태 변경] is_running 상태가 {prev_is_running}에서 {self.is_running}로 변경되었습니다.",
                                    'color': 'yellow'
                                })
                                prev_is_running = self.is_running
                                
                                # is_running이 False로 변경되었다면 대기 중단
                                if not self.is_running:
                                    self.add_log_message({
                                        'message': f"[대기 중단] is_running이 False로 변경되어 대기를 중단합니다.",
                                        'color': 'yellow'
                                    })
                                    break
                            
                            # 1초 대기
                            QThread.sleep(1)
                            remaining_seconds -= 1
                            
                            # 남은 시간 업데이트
                            time_str = self.format_time_remaining(remaining_seconds)
                            next_task_info = {
                                'next_task_number': i + 2,
                                'next_execution_time': next_time,
                                'wait_time': time_str
                            }
                            self.next_task_info.emit(next_task_info)
                        
                        # 대기 상태 확인 로그
                        if not self.is_running:
                            self.add_log_message({
                                'message': f"[대기 중단] 작업이 중지되었습니다. (is_running: {self.is_running})",
                                'color': 'yellow'
                            })
                            break
                        elif remaining_seconds <= 0:
                            self.add_log_message({
                                'message': "[대기 완료] 다음 작업을 시작합니다.",
                                'color': 'green'
                            })
                    
                except Exception as e:
                    error_msg = f"작업 실행 중 오류 발생: {str(e)}"
                    self.add_log_message({
                        'message': error_msg,
                        'color': 'red'
                    })
                    task['status'] = 'error'
                    task['error'] = str(e)
                    # 작업 오류 시그널 발생
                    self.task_error.emit(task, error_msg)
                
            # 모든 작업 완료 후 로그 추가
            if self.is_running:
                self.add_log_message({
                    'message': "모든 작업이 완료되었습니다.",
                    'color': 'green'
                })
                
                # 작업 반복 모드가 활성화되어 있으면 작업을 다시 시작
                if repeat_tasks:
                    # 작업 반복 시작 전 대기 시간 계산
                    wait_seconds = self.get_random_wait_time()
                    next_time = self.get_next_execution_time(wait_seconds)
                    time_remaining = self.format_time_remaining(wait_seconds)
                    
                    self.add_log_message({
                        'message': f"[작업 반복] 작업 반복 모드가 활성화되어 있습니다. {time_remaining} 후 처음부터 다시 시작합니다.",
                        'color': 'blue'
                    })
                    
                    # 다음 작업 정보 시그널 발생 (첫 번째 작업으로 설정)
                    next_task_info = {
                        'next_task_number': 1,  # 첫 번째 작업
                        'next_execution_time': next_time,
                        'wait_time': time_remaining
                    }
                    self.next_task_info.emit(next_task_info)
                    
                    # 대기 시작
                    remaining_seconds = wait_seconds
                    
                    # 대기 루프 시작 - is_running 상태를 지속적으로 확인
                    while remaining_seconds > 0 and self.is_running:
                        # 1초 대기
                        QThread.sleep(1)
                        remaining_seconds -= 1
                        
                        # 남은 시간 업데이트
                        time_str = self.format_time_remaining(remaining_seconds)
                        next_task_info = {
                            'next_task_number': 1,
                            'next_execution_time': next_time,
                            'wait_time': time_str
                        }
                        self.next_task_info.emit(next_task_info)
                    
                    # 대기 상태 확인 로그
                    if not self.is_running:
                        self.add_log_message({
                            'message': f"[대기 중단] 작업이 중지되었습니다. (is_running: {self.is_running})",
                            'color': 'yellow'
                        })
                        # 작업이 중간에 중지된 경우 시그널 발생 (비정상 완료)
                        self.all_tasks_completed.emit(False)
                    else:
                        # 대기 완료 후 작업 다시 시작
                        self.add_log_message({
                            'message': "[작업 반복] 처음부터 작업을 다시 시작합니다.",
                            'color': 'green'
                        })
                        
                        # 재귀적 호출 대신 시그널을 통해 메인 윈도우에 작업 재시작 요청
                        self.add_log_message({
                            'message': "[작업 반복] 재귀 호출 대신 시그널을 통해 작업 재시작을 요청합니다.",
                            'color': 'blue'
                        })
                        
                        # 작업 완료 시그널 발생 (특수 플래그 추가)
                        self.all_tasks_completed.emit(True)
                        
                        # 명시적으로 함수 종료
                        self.add_log_message({
                            'message': "[작업 종료] run 메서드를 종료합니다.",
                            'color': 'blue'
                        })
                        return
                else:
                    # 모든 작업이 정상적으로 완료된 경우 시그널 발생 (정상 완료)
                    self.add_log_message({
                        'message': "[작업 종료] 모든 작업이 완료되어 종료합니다.",
                        'color': 'green'
                    })
                    
                    # 작업 완료 후 상태 명시적으로 변경
                    self.is_running = False
                    self.add_log_message({
                        'message': f"[상태 변경] is_running 상태를 False로 변경했습니다. (현재: {self.is_running})",
                        'color': 'blue'
                    })
                    
                    # 완료 시그널 발생
                    self.all_tasks_completed.emit(True)
                    
                    # 명시적으로 함수 종료
                    self.add_log_message({
                        'message': "[작업 종료] run 메서드를 종료합니다.",
                        'color': 'blue'
                    })
                    return
            else:
                self.add_log_message({
                    'message': "작업이 중지되어 종료되었습니다.",
                    'color': 'yellow'
                })
                # 작업이 중간에 중지된 경우 시그널 발생 (비정상 완료)
                self.all_tasks_completed.emit(False)
                
            # 작업 완료 후 상태 업데이트
            self.is_running = False
            self.add_log_message({
                'message': f"[상태 업데이트] 작업 완료 후 is_running 상태가 False로 설정되었습니다. (현재: {self.is_running})",
                'color': 'blue'
            })

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
            "content-type": "application/x-www-form-urlencoded",
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
        
        # 필수 헤더 필드 확인
        required_headers = [
            "content-type", 
            "origin", 
            "referer", 
            "x-cafe-product", 
            "cookie", 
            "Cookie",
            "user-agent"
        ]
        
        # 필수 헤더 필드 확인
        missing_headers = [field for field in required_headers if field not in merged_headers or not merged_headers[field]]
        if missing_headers:
            self.add_log_message({
                'message': f"계정 '{account_id}'의 헤더 정보에 필수 필드가 누락되었습니다: {', '.join(missing_headers)}",
                'color': 'yellow'
            })
            
            # 필수 헤더가 누락된 경우 재로그인 시도
            if 'cookie' in missing_headers and 'Cookie' in missing_headers:
                self.add_log_message({
                    'message': f"계정 '{account_id}'의 쿠키 정보가 누락되어 재로그인을 시도합니다.",
                    'color': 'yellow'
                })
                
                # 재로그인 시도
                auth = NaverAuth()
                auth.set_credentials(account_id, self.main_window.accounts[account_id].get('pw', ''))
                if auth.login():
                    # 로그인 성공 시 헤더 정보 업데이트
                    new_headers = auth.get_headers()
                    self.main_window.accounts[account_id]['headers'] = new_headers
                    
                    # 새로운 헤더 정보로 병합
                    for key, value in new_headers.items():
                        if not key.startswith('_'):
                            merged_headers[key] = value
                            
                    self.add_log_message({
                        'message': f"계정 '{account_id}' 재로그인 성공! 헤더 정보가 업데이트되었습니다.",
                        'color': 'green'
                    })
                else:
                    raise ValueError(f"계정 '{account_id}'의 필수 헤더 정보 획득 실패")
            
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
        
        # 이미지 첨부 설정 추가
        cafe_info['use_image'] = cafe_settings.get('use_image', False)
        if cafe_info['use_image']:
            cafe_info['image_width'] = cafe_settings.get('image_width', 400)
            cafe_info['image_height'] = cafe_settings.get('image_height', 400)
        
        # 닉네임 변경 설정 추가
        cafe_info['use_nickname'] = cafe_settings.get('use_nickname', False)
        if cafe_info['use_nickname'] and 'nickname' in cafe_settings:
            cafe_info['nickname'] = cafe_settings['nickname']
        
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

    def generate_title_and_content(self, content_settings, cafe_settings, account_id):
        """제목 및 내용 생성
        
        Args:
            content_settings (dict): 콘텐츠 설정 정보
            cafe_settings (dict): 카페 설정 정보
            account_id (str): 계정 ID
            
        Returns:
            tuple: (제목, 내용)
        """
        
        # 필수 정보 확인
        if not content_settings:
            raise ValueError("콘텐츠 설정 정보가 없습니다.")
            
        # 프롬프트 확인
        prompt = content_settings.get('prompt', '')
        if not prompt:
            raise ValueError("AI 프롬프트가 설정되지 않았습니다.")
            
        # API 키 확인 및 디버깅
        api_key = content_settings.get('api_key', '')
        
        # UI에서 입력한 API 키 가져오기
        if hasattr(self.main_window, 'ai_api_key') and self.main_window.ai_api_key:
            api_key = self.main_window.ai_api_key
            self.add_log_message({
                'message': "메인 윈도우에서 API 키를 가져왔습니다.",
                'color': 'blue'
            })
                    
        if not api_key:
            self.add_log_message({
                'message': "OpenAI API 키가 설정되지 않았습니다. 작업 설정에서 API 키를 확인해주세요.",
                'color': 'red'
            })
            raise ValueError("OpenAI API 키가 설정되지 않았습니다.")
            
        # 글자수 제한 확인
        min_length = content_settings.get('min_length', 300)
        max_length = content_settings.get('max_length', 1000)
        
        # 콘텐츠 수집(중복방지) 설정 확인
        use_content_collection = content_settings.get('use_content_collection', True)
        content_collection_count = content_settings.get('content_collection_count', 20)
        
        # 로그 메시지 추가
        self.add_log_message({
            'message': f"AI 콘텐츠 생성 시작 (글자수: {min_length}~{max_length}자)",
            'color': 'blue'
        })
        
        try:
            # API 키 사용 확인 로그
            self.add_log_message({
                'message': f"API 키 사용: {api_key[:5]}...{api_key[-5:]}",
                'color': 'blue'
            })
            
            # 최근 게시글 정보 가져오기
            recent_posts_info = ""
            if use_content_collection:  # 콘텐츠 수집 사용 설정이 켜져 있을 때만 실행
                try:
                    # 카페 및 게시판 정보 가져오기
                    cafe_id = cafe_settings.get('cafe_id').get('id')
                    menu_id = cafe_settings.get('board_id')

                    if cafe_id and menu_id:
                        # 헤더 정보 가져오기
                        headers = self.get_account_header_info(account_id)
                        
                        if headers:
                            # CafeAPI 인스턴스 생성
                            cafe_api = CafeAPI(headers)
                            
                            # 설정된 개수만큼 최근 게시글 정보 가져오기
                            self.add_log_message({
                                'message': f"최근 {content_collection_count}개 게시글 정보 수집 중...",
                                'color': 'blue'
                            })
                            
                            recent_posts = cafe_api.get_board_title_and_content(cafe_id, menu_id, content_collection_count)
                            
                            if recent_posts:
                                recent_posts_info = f"\n\n[최근 게시글 정보]\n{recent_posts}\n\n위 게시글들과 중복되지 않는 새로운 내용으로 작성해주세요."
                                
                                self.add_log_message({
                                    'message': f"최근 {content_collection_count}개 게시글 정보 수집 완료",
                                    'color': 'green'
                                })
                            else:
                                self.add_log_message({
                                    'message': "최근 게시글 정보를 가져오지 못했습니다.",
                                    'color': 'yellow'
                                })
                        else:
                            self.add_log_message({
                                'message': "계정 헤더 정보를 가져오지 못했습니다.",
                                'color': 'yellow'
                            })
                    else:
                        self.add_log_message({
                            'message': "카페 ID 또는 메뉴 ID가 설정되지 않아 최근 게시글 정보를 가져오지 못했습니다.",
                            'color': 'yellow'
                        })
                except Exception as e:
                    self.add_log_message({
                        'message': f"최근 게시글 정보 수집 중 오류 발생: {str(e)}",
                        'color': 'yellow'
                    })
                    # 오류가 발생해도 계속 진행
            else:
                self.add_log_message({
                    'message': "콘텐츠 수집(중복방지) 기능이 비활성화되어 있습니다.",
                    'color': 'blue'
                })
            
            # 프롬프트에 최근 게시글 정보 추가
            if recent_posts_info:
                full_prompt = f"{prompt}{recent_posts_info}"
            else:
                full_prompt = prompt
            
            # AI 생성기 초기화 (API 키 전달)
            ai_generator = AIGenerator(api_key=api_key)
            
            # AI 호출하여 콘텐츠 생성
            self.add_log_message({
                'message': "AI 모델 호출 중...",
                'color': 'blue'
            })
            
            response = ai_generator.generate_content(full_prompt, min_length, max_length)
            
            # 응답에서 제목과 내용 분리
            if isinstance(response, dict) and 'title' in response and 'content' in response:
                title = response['title']
                content = response['content']
            else:
                # 응답 형식이 예상과 다른 경우 직접 분리 시도
                lines = response.strip().split('\n')
                title = lines[0].replace('제목:', '').replace('제목 :', '').strip()
                content = '\n'.join(lines[1:]).strip()
                
                # 제목이 너무 길면 잘라내기
                if len(title) > 100:
                    title = title[:100]
            
            # 콘텐츠 길이 확인
            content_length = len(content)
            if content_length < min_length:
                self.add_log_message({
                    'message': f"생성된 콘텐츠가 최소 글자수보다 짧습니다. ({content_length}/{min_length}자)",
                    'color': 'yellow'
                })
            elif content_length > max_length:
                # 최대 글자수를 초과하면 잘라내기
                content = content[:max_length]
                self.add_log_message({
                    'message': f"생성된 콘텐츠가 최대 글자수를 초과하여 잘렸습니다. ({content_length}/{max_length}자)",
                    'color': 'yellow'
                })
            
            # 로그 메시지 추가
            self.add_log_message({
                'message': f"AI 콘텐츠 생성 완료: 제목 '{title}' ({content_length}자)",
                'color': 'green'
            })
            
            return title, content
            
        except Exception as e:
            error_msg = f"AI 콘텐츠 생성 중 오류 발생: {str(e)}"
            self.add_log_message({
                'message': error_msg,
                'color': 'red'
            })
            raise ValueError(error_msg)

    def write_post(self, headers, cafe_info, title, content, reply_settings=None):
        """게시글 작성
        
        Args:
            headers (dict): 계정 헤더 정보
            cafe_info (dict): 카페 및 게시판 정보
            title (str): 게시글 제목
            content (str): 게시글 내용
            reply_settings (dict, optional): 댓글 설정 정보
            
        Returns:
            str: 게시글 URL
        """
        try:
            # 로그 메시지 추가
            self.add_log_message({
                'message': f"게시글 작성 시작: {cafe_info['cafe_name']} - {cafe_info['board_name']}",
                'color': 'blue'
            })
            
            # 헤더 타입 검사 및 변환 (추가 검증)
            validated_headers = {}
            for key, value in headers.items():
                # 내부 사용 필드는 제외 (_로 시작하는 필드)
                if key.startswith('_'):
                    continue
                    
                # 값이 문자열이나 바이트가 아닌 경우 문자열로 변환
                if isinstance(value, (str, bytes)):
                    validated_headers[key] = value
                else:
                    validated_headers[key] = str(value)
                    
            # 기본 헤더 설정
            default_headers = {
                "content-type": "application/x-www-form-urlencoded",
                "origin": "https://cafe.naver.com",
                "referer": "https://cafe.naver.com",
                "x-cafe-product": "pc",
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            }
            
            # 헤더 병합 (기본 헤더 + 검증된 헤더)
            validated_headers = {**default_headers, **validated_headers}
            
            # PostAPI 인스턴스 생성
            post_api = PostAPI(validated_headers)
            
            # 카페 ID와 게시판 ID 가져오기
            cafe_id = cafe_info['cafe_id']
            board_id = cafe_info['board_id']
            
            # cafe_id가 딕셔너리인 경우 처리
            if isinstance(cafe_id, dict) and 'id' in cafe_id:
                cafe_id = cafe_id['id']
            
            # 로그 메시지 추가
            self.add_log_message({
                'message': f"카페 ID: {cafe_id}, 게시판 ID: {board_id}",
                'color': 'blue'
            })
            
            # 이미지 첨부 여부 확인
            uploaded_images = []
            temp_files = []  # 임시 파일 추적
            
            # 계정 ID 가져오기
            account_id = None
            for task in self.tasks:
                if task.get('status') == 'running':
                    account_id = task.get('account_id')
                    break

            if cafe_info.get('use_image', False) and account_id:
                # 이미지 경로 설정 (imgs/계정ID)
                image_dir = os.path.join('imgs', str(account_id))
                
                # 이미지 폴더 확인
                if not os.path.exists(image_dir):
                    self.add_log_message({
                        'message': f"이미지 디렉토리가 존재하지 않습니다: {image_dir}",
                        'color': 'yellow'
                    })
                else:
                    # 이미지 파일 목록 가져오기
                    image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
                    if not image_files:
                        self.add_log_message({
                            'message': "사용 가능한 이미지가 없습니다.",
                            'color': 'yellow'
                        })
                    else:
                        # 2~3개 랜덤 선택
                        num_images = random.randint(2, 3)
                        selected_images = random.sample(image_files, min(num_images, len(image_files)))
                        
                        # 선택된 이미지 처리 및 업로드
                        for img_file in selected_images:
                            original_path = os.path.join(image_dir, img_file)
                            # 이미지 처리 및 임시 파일 생성
                            processed_path = post_api.process_image(original_path)
                            if processed_path:
                                temp_files.append(processed_path)
                                # 처리된 이미지 업로드
                                image_result = post_api.upload_image(cafe_id, processed_path)
                                if image_result:
                                    uploaded_images.append(image_result)
                                    self.add_log_message({
                                        'message': f"이미지 업로드 성공: {image_result['fileName']}",
                                        'color': 'green'
                                    })
                                else:
                                    self.add_log_message({
                                        'message': f"이미지 업로드 실패: {img_file}",
                                        'color': 'yellow'
                                    })
            
            # 게시글 작성
            self.add_log_message({
                'message': f"게시글 작성 중: {title}",
                'color': 'blue'
            })
            
            result = post_api.write_post(
                cafe_id=cafe_id,
                board_id=board_id,
                title=title,
                content=content,
                images=uploaded_images
            )
            
            # 임시 파일 정리
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except Exception as e:
                    self.add_log_message({
                        'message': f"임시 파일 삭제 실패: {str(e)}",
                        'color': 'yellow'
                    })
            
            # 게시글 작성 결과 처리
            if result and result.get('success', False) and 'article_url' in result:
                # URL 형식 변경 (cafes/ID/articles/ID -> cafe_url/ID)
                article_id = result.get('article_id')
                print("--------------------------------")
                print(cafe_info)
                print("--------------------------------")
                post_url = f"https://cafe.naver.com/{cafe_info['cafe_url']['url']}/{article_id}"
                
                # 게시글 작성 성공 메시지 (모니터 영역에 표시)
                self.add_log_message({
                    'message': f"게시글 작성 성공: {title}",
                    'color': 'green'
                })
                
                # 게시글 URL 메시지 (모니터 영역에 표시)
                self.add_log_message({
                    'message': f"게시글 URL: {post_url}",
                    'color': 'green'
                })
                
                # 게시글 모니터링 정보 업데이트
                if hasattr(self.main_window, 'monitor_widget'):
                    from datetime import datetime
                    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # 모니터링 데이터 구성
                    monitor_data = {
                        'timestamp': current_time,
                        'account_id': account_id,
                        'content': f"{title} (게시판: {cafe_info['board_name']})",
                        'url': post_url
                    }
                    
                    # 모니터 위젯에 데이터 추가 (QMetaObject.invokeMethod 사용)
                    if hasattr(self.main_window.monitor_widget, 'task_monitor'):
                        QMetaObject.invokeMethod(
                            self.main_window.monitor_widget,
                            "add_task_monitor_row",
                            Qt.QueuedConnection,
                            Q_ARG(QVariant, monitor_data)
                        )
                    else:
                        self.add_log_message({
                            'message': "task_monitor 위젯을 찾을 수 없습니다.",
                            'color': 'yellow'
                        })
                
                # 댓글 작성 처리
                if reply_settings and reply_settings.get('use_reply') and article_id:
                    self.add_log_message({
                        'message': "댓글 작성을 시작합니다.",
                        'color': 'blue'
                    })
                    
                    # 댓글 작성자 계정 정보
                    reply_account = reply_settings.get('account', {})
                    reply_account_id = reply_account.get('id')
                    reply_account_pw = reply_account.get('pw')
                    
                    # 댓글 작성자 계정으로 로그인하여 헤더 정보 가져오기
                    reply_headers = None
                    if reply_account_id and reply_account_pw:
                        auth = NaverAuth()
                        auth.set_credentials(reply_account_id, reply_account_pw)
                        if auth.login():
                            raw_headers = auth.get_headers()
                            
                            # 헤더 검증 및 변환
                            reply_headers = {}
                            for key, value in raw_headers.items():
                                # 내부 사용 필드는 제외
                                if key.startswith('_'):
                                    continue
                                    
                                # 값이 문자열이나 바이트가 아닌 경우 문자열로 변환
                                if isinstance(value, (str, bytes)):
                                    reply_headers[key] = value
                                else:
                                    reply_headers[key] = str(value)
                                    
                            # 기본 헤더 설정
                            default_headers = {
                                "content-type": "application/x-www-form-urlencoded",
                                "origin": "https://cafe.naver.com",
                                "referer": "https://cafe.naver.com",
                                "x-cafe-product": "pc",
                                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
                            }
                            
                            # 헤더 병합 (기본 헤더 + 검증된 헤더)
                            reply_headers = {**default_headers, **reply_headers}
                            
                            self.add_log_message({
                                'message': f"댓글 작성자 계정({reply_account_id}) 로그인 성공",
                                'color': 'green'
                            })
                        else:
                            self.add_log_message({
                                'message': f"댓글 작성자 계정({reply_account_id}) 로그인 실패",
                                'color': 'red'
                            })
                    
                    # 시나리오에 따라 댓글 작성
                    comment_set = []  # 현재 대화 세트를 저장할 리스트
                    last_comment_id = None  # 마지막 댓글 ID
                    current_set_start = None  # 현재 대화 세트의 시작 인덱스
                    
                    for i, scenario in enumerate(reply_settings.get('scenario', [])):
                        writer = scenario.get('writer')
                        content = scenario.get('content')
                        comment_type = scenario.get('type')
                        
                        # 새로운 댓글(comment)이 시작되면 새로운 대화 세트 시작
                        if comment_type == 'comment':
                            # 이전 대화 세트가 있었다면 초기화
                            if comment_set:
                                comment_set = []
                                last_comment_id = None
                            current_set_start = i  # 새로운 대화 세트의 시작 인덱스 저장
                            
                            # 댓글 작성자의 닉네임 변경 (새로운 대화 세트 시작 전)
                            if reply_settings.get('use_nickname') and writer == '댓글 작성자' and reply_headers:
                                try:
                                    # nickname.txt 파일에서 닉네임 목록 읽기
                                    nickname_file = "nickname.txt"
                                    if not os.path.exists(nickname_file):
                                        self.add_log_message({
                                            'message': f"{nickname_file} 파일이 존재하지 않습니다.",
                                            'color': 'yellow'
                                        })
                                        continue
                                        
                                    with open(nickname_file, 'r', encoding='utf-8') as f:
                                        nicknames = [line.strip() for line in f.readlines() if line.strip()]
                                        
                                    if not nicknames:
                                        self.add_log_message({
                                            'message': f"{nickname_file} 파일에 사용 가능한 닉네임이 없습니다.",
                                            'color': 'yellow'
                                        })
                                        continue
                                        
                                    # 현재 닉네임 가져오기
                                    cafe_api = CafeAPI(reply_headers)
                                    current_nickname = cafe_api.get_nickname(cafe_id)
                                    
                                    # 게시글 작성자의 닉네임 가져오기
                                    post_cafe_api = CafeAPI(validated_headers)
                                    post_nickname = post_cafe_api.get_nickname(cafe_id)
                                    
                                    # 현재 닉네임과 게시글 작성자의 닉네임을 제외한 닉네임 목록
                                    available_nicknames = [nick for nick in nicknames if nick != current_nickname and nick != post_nickname]
                                    
                                    if not available_nicknames:
                                        self.add_log_message({
                                            'message': "사용 가능한 닉네임이 없습니다.",
                                            'color': 'yellow'
                                        })
                                        continue
                                        
                                    # 랜덤으로 새 닉네임 선택
                                    new_nickname = random.choice(available_nicknames)
                                    
                                    # 닉네임 변경
                                    self.add_log_message({
                                        'message': f"닉네임 변경 시도: {current_nickname} -> {new_nickname}",
                                        'color': 'blue'
                                    })
                                    
                                    if cafe_api.update_nickname(cafe_id, new_nickname):
                                        self.add_log_message({
                                            'message': f"닉네임 변경 성공: {new_nickname}",
                                            'color': 'green'
                                        })
                                        time.sleep(random.randint(1, 2))  # 닉네임 변경 후 잠시 대기
                                    else:
                                        self.add_log_message({
                                            'message': "닉네임 변경 실패",
                                            'color': 'red'
                                        })
                                        
                                except Exception as e:
                                    self.add_log_message({
                                        'message': f"닉네임 변경 중 오류 발생: {str(e)}",
                                        'color': 'red'
                                    })
                            
                            # 대화 세트가 완료되는 조건 체크
                            is_last_scenario = i == len(reply_settings.get('scenario', [])) - 1  # 마지막 시나리오인지 확인
                            next_scenario = reply_settings.get('scenario', [])[i + 1] if i + 1 < len(reply_settings.get('scenario', [])) else None
                            is_new_comment_set = next_scenario and next_scenario.get('type') == 'comment'  # 다음 시나리오가 새로운 댓글인지 확인
                            
                            # 대화 세트가 완료되면 리스트 초기화
                            if is_last_scenario or is_new_comment_set:
                                comment_set = []
                                last_comment_id = None
                                current_set_start = None
                        
                        # 현재 시나리오를 대화 세트에 추가
                        comment_set.append(scenario)
                        
                        # 댓글 작성자 구분
                        if writer == '댓글 작성자' and reply_headers:
                            current_headers = reply_headers
                        elif writer == '게시글 작성자':
                            current_headers = validated_headers
                        else:
                            continue
                            
                        # ReplyAPI 인스턴스 생성
                        reply_api = ReplyAPI(current_headers)
                        
                        try:
                            # 댓글 타입에 따라 작성
                            if comment_type == 'comment':
                                # AI 생성 댓글 처리
                                if content == "AI가 생성한 친근한톤의 짧게 댓글":
                                    # 이전 댓글들을 분석하기 위해 현재까지의 댓글 세트 전달
                                    generated_content = self.generate_ai_comment(
                                        title=title,
                                        content=content,
                                        comment_type='comment',
                                        previous_comments=comment_set
                                    )
                                    if generated_content:
                                        content = generated_content
                                        # 생성된 내용을 시나리오에 저장
                                        scenario['generated_content'] = generated_content
                                    else:
                                        continue
                                
                                last_comment_id = reply_api.write_reply(cafe_id, article_id, content)
                                if last_comment_id:
                                    self.add_log_message({
                                        'message': f"댓글 작성 성공: {content[:30]}...",
                                        'color': 'green'
                                    })
                                    # 댓글 작성 후 1~2분 대기
                                    wait_time = random.randint(60, 120)
                                    self.add_log_message({
                                        'message': f"댓글 작성 후 {wait_time}초 대기",
                                        'color': 'blue'
                                    })
                                    time.sleep(wait_time)
                                else:
                                    self.add_log_message({
                                        'message': f"댓글 작성 실패",
                                        'color': 'red'
                                    })

                            elif comment_type == 'reply' and last_comment_id:
                                # AI 생성 대댓글 처리
                                if content == "└ AI가 생성한 친근한톤의 짧게 댓글":
                                    # 이전 댓글들을 분석하기 위해 현재까지의 댓글 세트 전달
                                    generated_content = self.generate_ai_comment(
                                        title=title,
                                        content=content,
                                        comment_type='reply',
                                        previous_comments=comment_set
                                    )
                                    if generated_content:
                                        content = generated_content
                                        # 생성된 내용을 시나리오에 저장
                                        scenario['generated_content'] = generated_content
                                    else:
                                        continue
                                        
                                result = reply_api.write_re_reply(cafe_id, article_id, last_comment_id, content)
                                if result:
                                    self.add_log_message({
                                        'message': f"대댓글 작성 성공: {content[:30]}...",
                                        'color': 'green'
                                    })
                                    # 대댓글 작성 후 1~2분 대기
                                    wait_time = random.randint(60, 120)
                                    self.add_log_message({
                                        'message': f"대댓글 작성 후 {wait_time}초 대기",
                                        'color': 'blue'
                                    })
                                    time.sleep(wait_time)
                                else:
                                    self.add_log_message({
                                        'message': f"대댓글 작성 실패: {content[:30]}...",
                                        'color': 'red'
                                    })
                                    
                        except Exception as e:
                            self.add_log_message({
                                'message': f"댓글 작성 중 오류 발생: {str(e)}",
                                'color': 'red'
                            })
                            
                        # 대화 세트가 완료되면 리스트 초기화
                        if is_last_scenario or is_new_comment_set:
                            comment_set = []
                
                # 계정 ID 가져오기 (run 메소드에서 전달된 account_id)
                account_id = None
                for task in self.tasks:
                    if task.get('status') == 'running':
                        account_id = task.get('account_id')
                        break
                
                # 작업 완료 메시지 (모니터 영역에 표시)
                if account_id:
                    self.add_log_message({
                        'message': f"작업 완료: {account_id}, 게시글: {title}",
                        'color': 'green'
                    })
                
                # 게시글 등록 완료 시그널 발생
                self.post_completed.emit(task)
                
                return post_url
            else:
                error_msg = "게시글 작성 실패"
                if result and 'message' in result:
                    error_msg += f": {result['message']}"
                    
                self.add_log_message({
                    'message': error_msg,
                    'color': 'red'
                })
                raise ValueError(error_msg)
                
        except Exception as e:
            error_msg = f"게시글 작성 중 오류 발생: {traceback.format_exc()}"
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

    def write_comment(self, headers, cafe_info, post_url, reply_settings):
        """댓글 작성 (현재 비활성화)
        
        Args:
            headers (dict): 계정 헤더 정보
            cafe_info (dict): 카페 및 게시판 정보
            post_url (str): 게시글 URL
            reply_settings (dict): 댓글 설정 정보
        """
        # 현재 비활성화 상태
        self.add_log_message({
            'message': "댓글 기능은 현재 비활성화 상태입니다.",
            'color': 'yellow'
        })
        return
    
    def change_nickname_after_post(self, headers, cafe_id):
        """게시글 작성 후 닉네임 변경
        
        Args:
            headers (dict): 계정 헤더 정보
            cafe_id (str): 카페 ID
        """
        try:
            # CafeAPI 인스턴스 생성
            cafe_api = CafeAPI(headers)
            
            # 현재 닉네임 가져오기
            current_nickname = cafe_api.get_nickname(cafe_id)
            if not current_nickname:
                self.add_log_message({
                    'message': "현재 닉네임 조회 실패",
                    'color': 'yellow'
                })
                return False
                
            # nickname.txt 파일에서 닉네임 목록 읽기
            nickname_file = "nickname.txt"
            if not os.path.exists(nickname_file):
                self.add_log_message({
                    'message': f"{nickname_file} 파일이 존재하지 않습니다.",
                    'color': 'yellow'
                })
                return False
                
            try:
                with open(nickname_file, 'r', encoding='utf-8') as f:
                    nicknames = [line.strip() for line in f.readlines() if line.strip()]
            except Exception as e:
                self.add_log_message({
                    'message': f"닉네임 파일 읽기 실패: {str(e)}",
                    'color': 'red'
                })
                return False
                
            # 현재 닉네임을 제외한 닉네임 목록에서 랜덤 선택
            available_nicknames = [nick for nick in nicknames if nick != current_nickname]
            if not available_nicknames:
                self.add_log_message({
                    'message': "사용 가능한 닉네임이 없습니다.",
                    'color': 'yellow'
                })
                return False
                
            # 랜덤으로 새 닉네임 선택
            new_nickname = random.choice(available_nicknames)
            
            # 닉네임 변경
            self.add_log_message({
                'message': f"닉네임 변경 시도: {current_nickname} -> {new_nickname}",
                'color': 'blue'
            })
            
            if cafe_api.update_nickname(cafe_id, new_nickname):
                self.add_log_message({
                    'message': f"닉네임 변경 성공: {new_nickname}",
                    'color': 'green'
                })
                return True
            else:
                self.add_log_message({
                    'message': "닉네임 변경 실패",
                    'color': 'red'
                })
                return False
                
        except Exception as e:
            self.add_log_message({
                'message': f"닉네임 변경 중 오류 발생: {str(e)}",
                'color': 'red'
            })
            return False

    def generate_ai_comment(self, title, content, comment_type='comment', previous_comments=None):
        """AI를 사용하여 댓글 또는 대댓글 생성
        
        Args:
            title (str): 게시글 제목
            content (str): 게시글 내용
            comment_type (str): 댓글 유형 ('comment' 또는 'reply')
            previous_comments (list): 이전 댓글 목록 (대화 세트)
            
        Returns:
            str: 생성된 댓글/대댓글 내용
        """
        try:
            # AI 생성기 인스턴스 생성
            ai_generator = OpenAIGenerator(api_key=self.main_window.ai_api_key)
            
            # 댓글 성향 리스트 정의
            comment_styles = [
                "20대 초반 여성의 귀엽고 발랄한 말투 (이모티콘 많이 사용, 'ㅋㅋㅋ' 자주 사용)",
                "30대 후반 주부의 경험담을 들려주는 조언하는 말투 (예: '저도 그랬었는데~')",
                "40대 직장인의 피곤하고 무뚝뚝한 말투 (짧고 건조한 문체)",
                "10대 학생의 줄임말 많이 쓰는 말투 (예: 'ㅎㅎ 완전 공감이에용')",
                "50대의 걱정스러운 부모님 말투 (조심스럽고 걱정하는 어투)",
                "20대 후반 직장인의 스트레스 받은 말투 (약간의 불만과 하소연)",
                "30대 초반의 전문가적인 말투 (정보를 공유하는 듯한 설명체)",
                "대학생의 장난스럽고 농담을 섞는 말투 (은어와 유행어 사용)",
                "주부의 요리/육아 경험을 공유하는 친근한 말투 (구체적인 경험담)",
                "취미생활 매니아의 열정적이고 전문적인 말투 (관련 용어 사용)"
            ]
            
            # 이전 댓글들의 대화 맥락 구성
            conversation_context = ""
            current_writer_role = ""  # 현재 작성자의 역할
            previous_writer_role = ""  # 이전 댓글 작성자의 역할
            
            if previous_comments and len(previous_comments) > 0:
                conversation_context = "\n이전 댓글들:\n"
                
                for idx, comment in enumerate(previous_comments, 1):
                    writer = comment.get('writer', '알 수 없음')
                    comment_content = comment.get('content', '')
                    comment_type_in_history = comment.get('type', 'comment')
                    
                    # AI 생성 댓글인 경우 실제 내용으로 대체
                    if "AI가 생성한" in comment_content:
                        # 이미 생성된 실제 내용이 있으면 그것을 사용
                        if hasattr(comment, 'generated_content') and comment.get('generated_content'):
                            comment_content = comment.get('generated_content')
                    
                    # 작성자 역할 설정
                    if writer == '댓글 작성자':
                        writer_role = "댓글 작성자"
                    elif writer == '게시글 작성자':
                        writer_role = "게시글 작성자"
                    else:
                        writer_role = writer
                    
                    # 현재 작성자 역할 설정
                    if idx == len(previous_comments):
                        previous_writer_role = writer_role
                    
                    prefix = "└" if comment_type_in_history == 'reply' else ">"
                    conversation_context += f"{prefix} {writer_role}: {comment_content}\n"
            
            # 현재 작성자 역할 결정 (이전 댓글 작성자와 다른 역할)
            if comment_type == 'reply':
                # 대댓글인 경우, 이전 댓글 작성자와 다른 역할을 맡음
                if previous_writer_role == "댓글 작성자":
                    current_writer_role = "게시글 작성자"
                else:
                    current_writer_role = "댓글 작성자"
            else:
                # 일반 댓글인 경우 기본적으로 댓글 작성자 역할
                current_writer_role = "댓글 작성자"
            
            # 댓글 유형에 따른 프롬프트 조정
            comment_type_desc = "댓글" if comment_type == 'comment' else "대댓글"
            
            if comment_type == 'comment':
                # 게시글에 대한 댓글 프롬프트
                prompt = f"""
네이버 카페의 게시글에 댓글을 작성해주세요.

[게시글 정보]
제목: {title}
내용: {content}

[요구사항]
1. 글자수는 50~150자 정도로 작성해주세요.
2. 아래 성향에 맞게 작성해주세요:
{random.choice(comment_styles)}
3. 게시글의 내용에 대한 의견이나 감상을 중심으로 작성해주세요.
4. 게시글 작성자의 상황이나 의견에 공감하는 내용을 포함해주세요.
5. 너무 형식적이거나 기계적인 답변은 피해주세요.
6. 이모지, 이모티콘은 절대 사용하지않습니다.
7. 개행문자를 적절히 사용해주세요.
8. 반드시 존댓말을 사용해주세요.
9. 당신은 '{current_writer_role}'입니다.
"""
            else:
                # 이전 댓글에 대한 대댓글 프롬프트
                prompt = f"""
네이버 카페의 댓글에 대댓글을 작성해주세요.

[게시글 정보]
제목: {title}
내용: {content}

{conversation_context}

[요구사항]
1. 글자수는 50~150자 정도로 작성해주세요.
2. 아래 성향에 맞게 작성해주세요:
{random.choice(comment_styles)}
3. 이전 댓글의 내용에 대한 반응이나 의견을 중심으로 작성해주세요.
4. 당신은 '{current_writer_role}'입니다. 이전 댓글 작성자는 '{previous_writer_role}'입니다.
5. 자연스러운 대화가 이어지도록 이전 댓글의 맥락을 유지해주세요.
6. 이전 댓글에서 언급된 내용에 대한 동의/반대 의견이나 추가 질문을 포함해주세요.
7. 너무 형식적이거나 기계적인 답변은 피해주세요.
8. 이모지, 이모티콘은 절대 사용하지않습니다.
9. 개행문자를 적절히 사용해주세요.
10. 반드시 존댓말을 사용해주세요.
11. 바로 직전 댓글에 대한 내용을 바탕으로 대화를 이어가세요.
12. 만약 이전 댓글에 질문이 있다면, 그 질문에 대한 답변을 포함해주세요.
13. 특히 이전에 한 내용과 동일한 내용을 작성하지 않도록 주의해주세요.
"""
            
            # AI로 댓글 생성
            generated_content = ai_generator.generate_comment(
                prompt=prompt,
                comment_type=comment_type,
                model="gpt-4o-mini"
            )
            
            self.add_log_message({
                'message': f"AI가 {comment_type_desc} 생성: {generated_content}",
                'color': 'blue'
            })
            
            return generated_content
            
        except Exception as e:
            self.add_log_message({
                'message': f"AI 댓글 생성 중 오류 발생: {str(e)}",
                'color': 'red'
            })
            return None



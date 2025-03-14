import subprocess
import time
import re
import socket

def toggle_usb_tethering(enable):
    # USB 테더링을 켜거나 끄는 명령어
    command = "adb shell svc usb setFunctions rndis" if enable else "adb shell svc usb setFunctions none"
    subprocess.run(command, shell=True)

def toggle_mobile_data(enable):
    # 모바일 데이터를 켜거나 끄는 명령어
    command = f"adb shell svc data {'enable' if enable else 'disable'}"
    subprocess.run(command, shell=True)

def get_current_ip():
    """현재 IP 주소를 조회하는 함수"""
    try:
        # 외부 IP 조회 서비스 사용
        response = subprocess.check_output("curl -s https://api.ipify.org", shell=True)
        ip = response.decode('utf-8').strip()
        return ip
    except Exception as e:
        print(f"IP 조회 중 오류 발생: {str(e)}")
        return "알 수 없음"

def is_tethering_enabled():
    """테더링 활성화 상태를 확인하는 함수"""
    try:
        # adb 명령어로 테더링 상태 확인
        result = subprocess.check_output("adb shell settings get global tether_dun_required", shell=True)
        result = result.decode('utf-8').strip()
        # 0이면 활성화, 1이면 비활성화 (기기마다 다를 수 있음)
        return result == "0"
    except Exception as e:
        print(f"테더링 상태 확인 중 오류 발생: {str(e)}")
        return False

def change_ip():
    print("IP 변경을 시작합니다...")
    
    # 현재 IP 확인
    old_ip = get_current_ip()
    print(f"현재 IP: {old_ip}")
    
    # 1. 모바일 데이터 끄기
    toggle_mobile_data(False)
    time.sleep(1)
    
    # 2. 모바일 데이터 켜기
    toggle_mobile_data(True)
    time.sleep(3)  # IP 변경에 시간이 필요할 수 있음
    
    # 변경된 IP 확인
    new_ip = get_current_ip()
    print(f"변경된 IP: {new_ip}")
    
    print("IP 변경이 완료되었습니다.")
    
    # IP 변경 여부 반환
    return old_ip != new_ip, old_ip, new_ip

if __name__ == "__main__":
    print(change_ip())


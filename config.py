import sys
import os

# --- 전역 설정 상수 ---
DAYS = ["월", "화", "수", "목", "금"]

# 요일별 교시 수 설정
PERIODS_PER_DAY = {
    "월": 6, "화": 7, "수": 6, "목": 7, "금": 6
}

MAX_PERIODS = 7

def resource_path(relative_path):
    """ 
    리소스 파일의 절대 경로를 반환합니다.
    PyInstaller로 패키징된 실행 파일(sys._MEIPASS)과 개발 환경 모두에서 작동합니다.
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
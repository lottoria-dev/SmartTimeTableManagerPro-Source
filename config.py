import sys
import os

# --- 전역 설정 상수 ---
# [신규] 2주차 스케줄 지원을 위한 주차 및 요일 분리
WEEKS = [1, 2]
BASE_DAYS = ["월", "화", "수", "목", "금"]

# "1주 월", "1주 화", ... , "2주 목", "2주 금" 형태로 10일치 요일 생성
DAYS = [f"{w}주 {d}" for w in WEEKS for d in BASE_DAYS]

# 요일별 교시 수 설정 (1주/2주 기본값 매핑)
PERIODS_PER_DAY = {}
for w in WEEKS:
    PERIODS_PER_DAY[f"{w}주 월"] = 6
    PERIODS_PER_DAY[f"{w}주 화"] = 7
    PERIODS_PER_DAY[f"{w}주 수"] = 6
    PERIODS_PER_DAY[f"{w}주 목"] = 7
    PERIODS_PER_DAY[f"{w}주 금"] = 6

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
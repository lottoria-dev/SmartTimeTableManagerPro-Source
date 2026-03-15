@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ========================================================
echo  스마트 시간표 매니저 프로 - 배포 파일 생성 스크립트
echo  (일반 패키징 모드 - Source Available 버전)
echo ========================================================

REM 0. 필수 파일 확인
if not exist main_pyqt.py (
    echo [오류] main_pyqt.py 파일이 없습니다.
    pause
    exit /b
)

REM 1. 필수 라이브러리 설치 (Cython 제거, PySide6 사용)
echo.
echo [1/4] 필수 라이브러리 설치 확인...
pip install pyinstaller PySide6 > nul

REM 2. 빌드 폴더 정리
echo.
echo [2/4] 이전 빌드 데이터 정리 중...
if exist build rd /s /q build
if exist dist rd /s /q dist
if exist *.spec del *.spec

REM 3. PyInstaller 패키징 (Cython 없이 직접 빌드)
echo.
echo [3/4] 실행 파일 생성 중...

REM --noconsole: 콘솔창 숨김
REM --onefile: 파일 하나로 통합
pyinstaller --noconsole --onefile ^
    --name "SmartTimetableManagerPro" ^
    --icon "icon.ico" ^
    --add-data "icon.ico;." ^
    --paths "." ^
    main_pyqt.py

if %errorlevel% neq 0 (
    echo.
    echo [오류] 빌드 중 에러가 발생했습니다.
    pause
    exit /b
)

REM 4. 무결성 검증 키(SHA256) 생성
echo.
echo [4/4] 프로그램 무결성 검증 값(SHA256) 생성 중...

if exist "dist\SmartTimetableManagerPro.exe" (
    certutil -hashfile "dist\SmartTimetableManagerPro.exe" SHA256 > "dist\checksum.txt"
    
    echo.
    echo --------------------------------------------------------
    echo [SHA256 해시값]
    type "dist\checksum.txt"
    echo --------------------------------------------------------
    echo 위 값을 GitHub 배포 페이지에 함께 적어두세요.
    echo 사용자가 다운로드한 파일이 원본인지 확인할 수 있습니다.
)

echo.
echo ========================================================
echo  빌드 완료! dist 폴더를 확인하세요.
echo ========================================================
pause
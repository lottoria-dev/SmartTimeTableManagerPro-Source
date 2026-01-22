@echo off
chcp 65001
echo ========================================================
echo  시간표 프로그램 EXE 빌드를 시작합니다.
echo ========================================================

:: 1. PyInstaller 설치 확인 및 설치
echo [1/3] PyInstaller 설치 확인 중...
pip install pyinstaller

:: 2. 빌드 명령어 실행
:: --noconsole: 검은색 콘솔창 뜨지 않게 함
:: --onefile: 실행 파일 하나로 뭉침
:: --icon: 실행 파일 아이콘 설정
:: --add-data: 아이콘과 로고 이미지를 내부 리소스로 포함 (Windows는 세미콜론 ; 사용)
:: --name: 생성될 exe 파일 이름 설정

echo.
echo [2/3] EXE 파일 생성 중... (시간이 조금 걸릴 수 있습니다)
pyinstaller --noconsole --onefile --clean ^
    --icon="icon.ico" ^
    --add-data "icon.ico;." ^
    --add-data "logo.png;." ^
    --name="SmartTimetable_AI" ^
    main_pyqt.py

:: 3. 결과 안내
echo.
if exist "dist\SmartTimetable_AI.exe" (
    echo [3/3] 빌드 성공! 
    echo 'dist' 폴더 안에 'SmartTimetable_AI.exe' 파일이 생성되었습니다.
    explorer "dist"
) else (
    echo [오류] 빌드에 실패했습니다. 위의 에러 메시지를 확인해주세요.
)

pause
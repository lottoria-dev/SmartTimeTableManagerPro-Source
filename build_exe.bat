@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ========================================================
echo  스마트 시간표 매니저 프로 - 배포 파일 생성 스크립트
echo  - Cython 컴파일 난독화 + PyInstaller 패키징 -
echo ========================================================

REM [안전 장치 1] 이전 실행 실패로 인한 잔여 백업 확인 및 복구
if exist src_backup (
    echo.
    echo - 경고 - 비정상 종료된 이전 빌드 데이터를 감지했습니다.
    echo - 복구 - 원본 소스 코드를 복구 중입니다...
    
    set "MODULES=logic ai_mover csv_manager config"
    for %%m in (logic ai_mover csv_manager config) do (
        if exist src_backup\%%m.py (
            move /y src_backup\%%m.py . > nul
            echo   복구됨: %%m.py
        )
    )
    rd /s /q src_backup
    echo - 완료 - 복구가 완료되었습니다. 빌드를 시작합니다.
)

REM 0. 현재 폴더 확인 및 파일 존재 여부 검사
echo.
echo - 0/6 - 소스 코드 파일 확인 중...
echo 현재 작업 경로: %CD%

set "MISSING_FILES=0"
for %%f in (main_pyqt.py logic.py ai_mover.py csv_manager.py config.py gui_pyqt.py gui_styles.py gui_components.py icon.ico) do (
    if not exist "%%f" (
        echo - 오류 - 필수 파일이 없습니다: %%f
        set "MISSING_FILES=1"
    )
)

if "!MISSING_FILES!"=="1" (
    echo.
    echo -------------------------------------------------------------
    echo - 치명적 오류 - 일부 소스 파일이 현재 폴더에 없습니다.
    echo -------------------------------------------------------------
    pause
    exit /b 1
)

REM 1. 필수 라이브러리 설치
echo.
echo - 1/6 - 필수 라이브러리 설치 확인...
pip install pyinstaller PyQt6 Cython setuptools > nul

REM 2. 빌드 폴더 정리
echo.
echo - 2/6 - 이전 빌드 폴더 정리 중...
if exist build rd /s /q build
if exist dist rd /s /q dist
if exist *.spec del *.spec
if exist *.c del *.c
if exist *.pyd del *.pyd
if exist build_cython_setup.py del build_cython_setup.py

REM 3. Cython을 이용한 핵심 로직 컴파일
echo.
echo - 3/6 - 핵심 로직 컴파일 - 난독화 - 시도 중...

set "MODULES=logic ai_mover csv_manager config"

REM setup.py 동적 생성
echo from setuptools import setup > build_cython_setup.py
echo from Cython.Build import cythonize >> build_cython_setup.py
echo. >> build_cython_setup.py
echo setup(ext_modules=cythonize([ >> build_cython_setup.py
echo     "logic.py", "ai_mover.py", "csv_manager.py", "config.py" >> build_cython_setup.py
echo ], compiler_directives={'language_level': '3'})) >> build_cython_setup.py

python build_cython_setup.py build_ext --inplace > build_log.txt 2>&1
set CYTHON_EXIT_CODE=%errorlevel%

if %CYTHON_EXIT_CODE% neq 0 (
    echo.
    echo - 경고 - Cython 빌드 실패. 일반 모드로 진행합니다.
    set "CYTHON_SUCCESS=0"
) else (
    set "CYTHON_SUCCESS=1"
    for %%m in (%MODULES%) do (
        if not exist %%m*.pyd set "CYTHON_SUCCESS=0"
    )
)

if "!CYTHON_SUCCESS!"=="1" (
    echo - 성공 - 핵심 모듈 컴파일 완료.
    
    REM 원본 .py 파일 백업 (PyInstaller가 .pyd를 쓰도록 강제)
    if not exist src_backup mkdir src_backup
    for %%m in (%MODULES%) do (
        copy %%m.py src_backup\ > nul
        del %%m.py
    )
)

REM 4. PyInstaller 패키징
echo.
echo - 4/6 - PyInstaller로 실행 파일 생성 중...

pyinstaller --noconsole --onefile ^
    --name "SmartTimetableManagerPro" ^
    --icon "icon.ico" ^
    --add-data "icon.ico;." ^
    --paths "." ^
    --hidden-import "logic" ^
    --hidden-import "ai_mover" ^
    --hidden-import "csv_manager" ^
    --hidden-import "config" ^
    main_pyqt.py

set BUILD_ERROR=%errorlevel%
if %BUILD_ERROR% neq 0 (
    echo.
    echo - 오류 - PyInstaller 빌드 중 에러가 발생했습니다.
)

REM 5. 정리 및 복구 (RESTORE)
echo.
echo - 5/6 - 작업 환경 복구 및 정리 중...

if "!CYTHON_SUCCESS!"=="1" (
    REM 백업해둔 원본 소스 복구
    for %%m in (%MODULES%) do (
        if exist src_backup\%%m.py (
            move /y src_backup\%%m.py . > nul
        )
    )
    if exist src_backup rd /s /q src_backup
)

if exist build_cython_setup.py del build_cython_setup.py
if exist *.c del *.c
if exist *.pyd del *.pyd
if exist build_log.txt del build_log.txt

REM 6. 무결성 검증 키(SHA256) 생성
echo.
echo - 6/6 - 프로그램 무결성 검증 값(SHA256) 생성 중...

if exist "dist\SmartTimetableManagerPro.exe" (
    REM 윈도우 기본 명령어 certutil 사용
    certutil -hashfile "dist\SmartTimetableManagerPro.exe" SHA256 > "dist\checksum.txt"
    
    echo.
    echo --------------------------------------------------------
    echo [SHA256 해시값]
    type "dist\checksum.txt"
    echo --------------------------------------------------------
    echo.
    echo 위 값을 복사하여 GitHub 배포 페이지에 함께 적어두세요.
    echo - dist\checksum.txt 파일에도 저장되었습니다 -
) else (
    echo [경고] 실행 파일이 없어 해시를 생성하지 못했습니다.
)

echo.
echo ========================================================
if %BUILD_ERROR% equ 0 (
    echo  - 빌드 완료 - dist 폴더를 확인하세요.
) else (
    echo  - 빌드 실패 - 오류 로그를 확인하세요. 원본 파일은 복구되었습니다.
)
echo ========================================================
pause
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont, QIcon

from gui_pyqt import TimetableWindow
import config

def main():
    app = QApplication(sys.argv)
    
    # [v1.2.0] 아이콘 설정
    # 어플리케이션 레벨에서 아이콘을 설정하면 메인 윈도우 및 도움말/로그 등 모든 팝업창에 공통 적용됩니다.
    # config.resource_path를 통해 PyInstaller 패키징 시에도 아이콘을 정상적으로 로드합니다.
    app.setWindowIcon(QIcon(config.resource_path("icon.ico")))
    
    # 전역 폰트 설정 (시스템 폰트와 조화)
    font = QFont("Malgun Gothic", 10)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)
    
    window = TimetableWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
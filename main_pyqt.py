import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont

from gui_pyqt import TimetableWindow

def main():
    app = QApplication(sys.argv)
    
    # 전역 폰트 설정 (시스템 폰트와 조화)
    font = QFont("Malgun Gothic", 10)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)
    
    window = TimetableWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

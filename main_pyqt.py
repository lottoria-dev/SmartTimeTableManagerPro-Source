import sys
from PySide6.QtWidgets import QApplication, QDialog
from PySide6.QtGui import QFont, QIcon
from PySide6.QtCore import QObject, QEvent

from gui_pyqt import TimetableWindow
import config

class DialogOpacityFilter(QObject):
    """프로그램 내에서 생성되는 모든 팝업창을 감지하여 투명도를 자동으로 부여하는 전역 필터"""
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Show:
            if isinstance(obj, QDialog):
                obj.setWindowOpacity(0.95)
        return False

def main():
    app = QApplication(sys.argv)
    
    # [v1.2.0] 아이콘 설정
    app.setWindowIcon(QIcon(config.resource_path("icon.ico")))
    
    # 전역 폰트 설정 (시스템 폰트와 조화)
    font = QFont("Malgun Gothic", 10)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)
    
    # [신규] 전역 투명도 필터 적용
    # 이 코드 덕분에 QMessageBox 등 일일이 지정하기 어려운 창들도 한꺼번에 0.95 투명도를 가집니다!
    opacity_filter = DialogOpacityFilter()
    app.installEventFilter(opacity_filter)
    
    window = TimetableWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
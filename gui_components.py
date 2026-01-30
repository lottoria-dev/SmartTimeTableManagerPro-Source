from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTextEdit, QTextBrowser, QPushButton, QFrame, 
    QLabel, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal

class HelpDialog(QDialog):
    """도움말 팝업창"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("사용법 안내")
        self.resize(650, 600)
        self.setStyleSheet("background-color: white; color: #333333;")
        
        layout = QVBoxLayout(self)
        
        # [수정] QTextEdit -> QTextBrowser로 변경 (setOpenExternalLinks 지원)
        text_edit = QTextBrowser()
        # [중요] 링크 클릭 시 시스템 기본 브라우저에서 열리도록 설정
        text_edit.setOpenExternalLinks(True)
        text_edit.setFrameShape(QFrame.Shape.NoFrame)
        text_edit.setStyleSheet("font-family: 'Malgun Gothic'; font-size: 11pt; color: #333333; background-color: white;")
        
        # [수정] 링크 태그(<a>) 적용
        help_content = """
<h2>📖 스마트 시간표 매니저 사용법</h2>
<hr>
<h3>1. 기본 사용법</h3>
<ul>
    <li><b>📂 불러오기:</b> CSV 형식의 시간표 파일을 불러옵니다.<br>
    <span style="font-size: 10pt; color: #666;">
    ※ 분리형, 병합형, 저장본 모두 지원<br>
    ※ <a href="https://mathtime.kr/?page=timetable" style="color: #3b82f6; text-decoration: none;"><b>https://mathtime.kr/?page=timetable</b></a>의 예시 양식 활용 권장<br>
    ※ 엑셀에서 [내보내기] > [CSV(쉼표로 분리)]로 저장하여 사용
    </span></li>
    <li><b>보기 방식:</b> 요일별, 교사별 등 다양한 형태로 확인 가능하며, <b>📋 복사</b> 버튼으로 엑셀/한글에 바로 붙여넣을 수 있습니다.</li>
    <li><b>💾 저장:</b> 작업 내용을 언제든 CSV 파일로 백업할 수 있습니다.</li>
</ul>

<h3>2. 작업 모드 상세</h3>
<ul>
    <li><b>👁️ 조회 모드:</b> 
        <ul>
            <li>수업 클릭 시 해당 교사의 주간 일정이 <span style="color:blue; font-weight:bold;">파란색</span>으로 강조됩니다.</li>
            <li>마우스 우클릭으로 셀을 <b>🔒 잠금/해제</b>하여 실수를 방지합니다.</li>
            <li>3연강 이상 교사는 <span style="color:purple; font-weight:bold;">보라색 텍스트</span>로 표시됩니다.</li>
            <li>교사별 조회 상태에서는 교사명이 특수문자나 숫자로만 구성된 경우는 제외합니다.</li>
            <li>교과별 조회 상태에서는 가급적 유사교과끼리 묶어서 출력합니다. </li>
        </ul>
    </li>
    <li><b>🔄 맞교환 모드:</b> 
        <ul>
            <li>바꿀 두 수업을 차례로 클릭합니다.</li>
            <li>첫 번째 선택 시 이동 가능 시간은 <span style="color:green; font-weight:bold;">초록색</span>, 충돌 예상 시간은 <span style="color:red; font-weight:bold;">분홍색</span>으로 표시됩니다.</li>
        </ul>
    </li>
    <li><b>🛠️ 보강 모드:</b> 결강 수업 선택 → 상단 메뉴에서 대체 교사 선택 → <b>'배정'</b> 클릭.</li>
    <li><b>🔗 연쇄 이동 모드 (CHAIN):</b> 
        <ul>
            <li>수업을 빈 공간이나 다른 수업 자리로 이동시킵니다.</li>
            <li>밀려난 수업을 계속해서 이동시키며 연쇄적으로 정리합니다.</li>
        </ul>
    </li>
    <li><b>🤖 AI 자동 모드:</b> 
        <ul>
            <li>같은 요일 내에서 <b>[출발할 수업]</b>과 <b>[도착할 시간]</b>을 클릭하면, AI가 최적의 이동 경로를 찾아 자동 재배치합니다.</li>
        </ul>
    </li>
</ul>

<h3>💡 팁 & 정보</h3>
<ul>
    <li>실수했을 땐 <b>↩ 실행취소</b>, 선택을 취소할 땐 <b>🚫 선택해제</b>(ESC 키)를 누르세요.</li>
</ul>
<hr>
<div style="font-size: 10pt; color: #555; line-height: 1.4;">
    <b>■ 개발자 정보</b><br>
    - 개발일: 2026.01.30<br>
    - 문의: trsketch@gmail.com<br>
    - 본 프로그램은 무단 재배포 및 상업적 이용이 금지되어 있습니다.<br>
    © Copyright 2026. All rights reserved.
</div>
"""
        text_edit.setHtml(help_content)
        layout.addWidget(text_edit)
        
        btn_close = QPushButton("닫기")
        btn_close.clicked.connect(self.accept)
        btn_close.setStyleSheet("""
            QPushButton { background-color: #3b82f6; color: white; border-radius: 5px; padding: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #2563eb; }
        """)
        layout.addWidget(btn_close)


class ClickableFrame(QFrame):
    """클릭 이벤트를 처리하는 커스텀 프레임 (시간표 셀)"""
    clicked = pyqtSignal(object)
    right_clicked = pyqtSignal(object)

    def __init__(self, data_key, parent=None):
        super().__init__(parent)
        self.data_key = data_key
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setObjectName("Cell")
        
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        # [수정] 셀의 최소 높이를 더 줄여 수직 공간 확보 (38 -> 32)
        self.setMinimumHeight(32)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # [수정] 텍스트가 수직 중앙에 오밀조밀하게 모이도록 상단 스트레치 추가
        self.layout.addStretch(1)
        
        self.lbl_main = QLabel()
        self.lbl_main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_main.setWordWrap(True)
        # [수정] 폰트 크기 10px, 하단 마진 음수(-1px)로 줄여서 교사와 밀착
        self.lbl_main.setStyleSheet("font-weight: bold; font-size: 10px; border: none; background-color: transparent; padding: 0px; margin: 0px; margin-bottom: -1px;")
        
        self.lbl_sub = QLabel()
        self.lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # [수정] 폰트 크기 9px, 상단 마진 음수(-1px)로 줄여서 교과와 밀착
        self.lbl_sub.setStyleSheet("color: #6b7280; font-size: 9px; border: none; background-color: transparent; padding: 0px; margin: 0px; margin-top: -1px;")
        
        self.layout.addWidget(self.lbl_main)
        self.layout.addWidget(self.lbl_sub)
        
        # [수정] 하단 스트레치 추가
        self.layout.addStretch(1)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.data_key)
        elif event.button() == Qt.MouseButton.RightButton:
            self.right_clicked.emit(self.data_key)

    def set_content(self, main_text, sub_text, bg_color, border_color=None, border_width=1, text_color=None):
        self.lbl_main.setText(main_text)
        self.lbl_sub.setText(sub_text)
        
        if not text_color:
            text_color = "#1f2937"
        
        # [수정] text_color 인자를 받아 글자색 동적 적용
        main_style = f"font-size: 10px; border: none; background-color: transparent; padding: 0px; margin: 0px; margin-bottom: -1px; font-weight: bold; color: {text_color};"
        
        self.lbl_main.setStyleSheet(main_style)

        style = f"background-color: {bg_color}; border-radius: 4px;"
        if border_color:
            style += f" border: {border_width}px solid {border_color};"
        else:
            style += " border: 1px solid #e5e7eb;"
        style += " padding: 0px;"
            
        self.setStyleSheet(f"QFrame#Cell {{ {style} }}")
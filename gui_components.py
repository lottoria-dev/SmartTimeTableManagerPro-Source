from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QTextBrowser, QPushButton, QFrame, 
    QLabel, QSizePolicy, QTreeWidget, QTreeWidgetItem, QComboBox, QApplication
)
from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QDrag

class HelpDialog(QDialog):
    """도움말 팝업창"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("사용법 안내 - v2.6.1")
        self.resize(650, 600)
        self.setStyleSheet("background-color: white; color: #333333;")
        
        layout = QVBoxLayout(self)
        
        text_edit = QTextBrowser()
        text_edit.setOpenExternalLinks(True)
        text_edit.setFrameShape(QFrame.Shape.NoFrame)
        text_edit.setStyleSheet("font-family: 'Malgun Gothic'; font-size: 11pt; color: #333333; background-color: white;")
        
        # [수정] 개발자 정보에 lottoria 적용
        help_content = """
<h2>📖 스마트 시간표 매니저(SmartTimetableManagerPro) v2.6.1</h2>
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
    <li><b>📜 내역:</b> 변경된 내역을 별도 창에서 확인합니다.</li>
</ul>

<h3>2. 작업 모드 상세</h3>
<ul>
    <li><b>조회 모드:</b> 
        <ul>
            <li>수업 클릭 시 해당 교사의 주간 일정이 <span style="color:blue; font-weight:bold;">파란색</span>으로 강조됩니다.</li>
            <li>마우스 우클릭으로 셀을 <b>🔒 잠금/해제</b>하여 실수를 방지합니다.</li>
            <li>3연강 이상 교사는 <span style="color:purple; font-weight:bold;">보라색 텍스트</span>로 표시됩니다.</li>
        </ul>
    </li>
    <li><b>맞교환 모드:</b> 
        <ul>
            <li>바꿀 두 수업을 차례로 클릭하거나 <b>드래그 앤 드롭</b>합니다.</li>
            <li>첫 번째 선택 시 이동 가능 시간은 <span style="color:green; font-weight:bold;">초록색</span>, 충돌 예상 시간은 <span style="color:red; font-weight:bold;">분홍색</span>으로 표시됩니다.</li>
        </ul>
    </li>
    <li><b>보강 모드:</b> 결강 수업 선택 → 상단 메뉴에서 대체 교사 선택 → <b>'배정'</b> 클릭.</li>
    <li><b>연쇄 이동 모드 (CHAIN):</b> 
        <ul>
            <li>수업을 빈 공간이나 다른 수업 자리로 클릭하거나 <b>드래그 앤 드롭</b>하여 이동시킵니다.</li>
            <li>밀려난 수업을 계속해서 이동시키며 연쇄적으로 정리합니다.</li>
        </ul>
    </li>
    <li><b>AI 자동 모드:</b> 
        <ul>
            <li><span style="color:red; font-weight:bold;">※ AI 모드는 같은 요일 내에서만 이동이 가능합니다.</span></li>
            <li><b>[출발할 수업]</b>과 <b>[도착할 시간]</b>을 클릭하거나 <b>드래그 앤 드롭</b>하면, AI가 최적의 이동 경로를 찾아 자동 재배치합니다.</li>
        </ul>
    </li>
</ul>

<hr>
<div style="font-size: 10pt; color: #555; line-height: 1.4;">
    <b>■ 단축키 안내</b><br>
    - [Ctrl + O] 불러오기 / [Ctrl + S] 저장<br>
    - [Ctrl + Z] 실행취소 / [Ctrl + C] 클립보드 복사<br>
    - [1 ~ 5] 모드 빠른 전환<br>
    <br>
    <b>■ 개발자 정보</b><br>
    - 버전: 2.6.1<br>
    - 최종 업데이트: 2026.04.04.<br>
    - special thanks to [haruka12, pucca2816]<br>
    - 문의: mathtime.ai@gmail.com<br>
    - 정식 배포 페이지를 제외한 곳에서 임의의 수정 및 재배포를 금지합니다.<br>
    © Copyright 2026 lottoria-dev. All rights reserved.
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

class LogDialog(QDialog):
    """변경 내역을 보여주는 별도 팝업창"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("변경 내역 (Log)")
        self.resize(500, 600)
        self.setStyleSheet("background-color: white; color: #333333;")
        
        layout = QVBoxLayout(self)
        
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["구분", "학반", "내용"])
        self.tree_widget.header().resizeSection(0, 60)
        self.tree_widget.header().resizeSection(1, 70)
        self.tree_widget.setIndentation(0)
        self.tree_widget.setAlternatingRowColors(True)
        self.tree_widget.setStyleSheet("color: #1f2937;")
        layout.addWidget(self.tree_widget)
        
        btn_layout = QHBoxLayout()
        
        self.btn_copy_stats = QPushButton("📊 결보강 통계 엑셀 복사")
        self.btn_copy_stats.clicked.connect(self.copy_stats)
        self.btn_copy_stats.setStyleSheet("""
            QPushButton { background-color: #10b981; color: white; border-radius: 5px; padding: 6px; font-weight: bold; }
            QPushButton:hover { background-color: #059669; }
        """)
        btn_layout.addWidget(self.btn_copy_stats)

        btn_close = QPushButton("닫기")
        btn_close.clicked.connect(self.accept)
        btn_close.setStyleSheet("""
            QPushButton { background-color: #6b7280; color: white; border-radius: 5px; padding: 6px; }
            QPushButton:hover { background-color: #4b5563; }
        """)
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)

    def copy_stats(self):
        if self.parent() and hasattr(self.parent(), 'copy_stats_to_clipboard'):
            self.parent().copy_stats_to_clipboard()

    def update_logs(self, logs):
        self.tree_widget.clear()
        for log in logs:
            if isinstance(log, dict):
                item = QTreeWidgetItem([str(log.get('type','')), str(log.get('class','')), str(log.get('desc',''))])
                self.tree_widget.addTopLevelItem(item)
        
        if self.tree_widget.topLevelItemCount() > 0:
            last_item = self.tree_widget.topLevelItem(self.tree_widget.topLevelItemCount() - 1)
            self.tree_widget.scrollToItem(last_item)

class ClickableFrame(QFrame):
    """클릭 및 드래그 앤 드롭 이벤트를 처리하는 커스텀 프레임 (시간표 셀)"""
    clicked = Signal(object)
    right_clicked = Signal(object)
    cell_dropped = Signal(object, object) # [업데이트] 드롭 시그널 (src_key, tgt_key)

    def __init__(self, data_key, parent=None):
        super().__init__(parent)
        self.data_key = data_key
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setObjectName("Cell")
        
        self.setAcceptDrops(True) # [업데이트] 드롭 허용
        self.drag_start_position = None
        
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        self.setMinimumHeight(30)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.layout.addStretch(1)
        
        self.lbl_main = QLabel()
        self.lbl_main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_main.setWordWrap(True)
        self.lbl_main.setStyleSheet("font-weight: bold; font-size: 10px; border: none; background-color: transparent; padding: 0px; margin: 0px; margin-bottom: -1px;")
        
        self.lbl_sub = QLabel()
        self.lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_sub.setStyleSheet("color: #6b7280; font-size: 9px; border: none; background-color: transparent; padding: 0px; margin: 0px; margin-top: -1px;")
        
        self.layout.addWidget(self.lbl_main)
        self.layout.addWidget(self.lbl_sub)
        
        self.layout.addStretch(1)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos() # [업데이트] 드래그 시작점 저장
            self.clicked.emit(self.data_key) # 기존 클릭 처리도 수행하여 선택 상태 반영
        elif event.button() == Qt.MouseButton.RightButton:
            self.right_clicked.emit(self.data_key)

    # [업데이트] 마우스 이동 감지하여 드래그 앤 드롭 시작
    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton): return
        if not self.drag_start_position: return
        
        # 드래그 시작 임계값 확인
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
            
        drag = QDrag(self)
        mime_data = QMimeData()
        
        # 키를 문자열로 직렬화하여 전송
        key_str = "|".join(map(str, self.data_key))
        mime_data.setText(key_str)
        drag.setMimeData(mime_data)
        
        # 드래그 실행 (커서는 시스템 기본 이동 아이콘으로 변경됨)
        drag.exec(Qt.DropAction.MoveAction)

    # [업데이트] 드롭 이벤트 처리 허용
    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    # [업데이트] 드롭 발생 시 목적지 데이터 파싱 및 시그널 에밋
    def dropEvent(self, event):
        src_key_str = event.mimeData().text()
        src_parts = src_key_str.split('|')
        
        # 직렬화된 키 복원
        if src_parts[0] == "TEACHER_VIEW":
            src_key = ("TEACHER_VIEW", src_parts[1], src_parts[2], int(src_parts[3]))
        else:
            src_key = (src_parts[0], src_parts[1], src_parts[2], int(src_parts[3]))
            
        self.cell_dropped.emit(src_key, self.data_key)
        event.acceptProposedAction()

    def set_content(self, main_text, sub_text, bg_color, border_color=None, border_width=1, text_color=None):
        self.lbl_main.setText(main_text)
        self.lbl_sub.setText(sub_text)
        
        if not text_color:
            text_color = "#1f2937"
        
        main_style = f"font-size: 10px; border: none; background-color: transparent; padding: 0px; margin: 0px; margin-bottom: -1px; font-weight: bold; color: {text_color};"
        self.lbl_main.setStyleSheet(main_style)

        base_style = f"""
            background-color: {bg_color}; 
            border-radius: 4px;
        """
        if border_color:
            base_style += f" border: {border_width}px solid {border_color};"
        else:
            base_style += " border: 1px solid #e5e7eb;"
        base_style += " padding: 0px;"
        
        hover_style = f"""
            QFrame#Cell:hover {{
                border: 2px solid #9ca3af;
                background-color: {bg_color}; 
            }}
        """

        self.setStyleSheet(f"QFrame#Cell {{ {base_style} }} {hover_style}")
        
class DayRoutineDialog(QDialog):
    """요일 전체 일과를 덮어쓰는 기능 팝업창"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("요일 일과 변경")
        self.resize(350, 160)
        self.setStyleSheet("background-color: white; color: #333333;")
        
        layout = QVBoxLayout(self)
        
        lbl_info = QLabel("특정 요일의 전체 시간표를 다른 요일에 덮어씁니다.\n(학사일정 변경 전용 - 개별 결보강 통계에서 제외됨)")
        lbl_info.setStyleSheet("color: #4b5563; font-size: 10pt; margin-bottom: 10px; font-weight: bold;")
        layout.addWidget(lbl_info)
        
        form_layout = QHBoxLayout()
        
        self.combo_src = QComboBox()
        self.combo_src.addItems(["월", "화", "수", "목", "금"])
        
        lbl_arrow = QLabel(" ➔ ")
        lbl_arrow.setStyleSheet("font-weight: bold; color: #3b82f6;")
        
        self.combo_tgt = QComboBox()
        self.combo_tgt.addItems(["월", "화", "수", "목", "금"])
        
        form_layout.addWidget(QLabel("가져올 일과:"))
        form_layout.addWidget(self.combo_src)
        form_layout.addWidget(lbl_arrow)
        form_layout.addWidget(QLabel("덮어쓸 요일:"))
        form_layout.addWidget(self.combo_tgt)
        
        layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        btn_apply = QPushButton("적용하기")
        btn_apply.setStyleSheet("""
            QPushButton { background-color: #ef4444; color: white; font-weight: bold; padding: 6px; border-radius: 4px; }
            QPushButton:hover { background-color: #dc2626; }
        """)
        btn_apply.clicked.connect(self.accept)
        
        btn_cancel = QPushButton("취소")
        btn_cancel.setStyleSheet("""
            QPushButton { background-color: #e5e7eb; color: #374151; padding: 6px; border-radius: 4px; }
            QPushButton:hover { background-color: #d1d5db; }
        """)
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_apply)
        
        layout.addStretch()
        layout.addLayout(btn_layout)
        
    def get_days(self):
        return self.combo_src.currentText(), self.combo_tgt.currentText()
import sys
import os
import re  # 정규표현식 사용을 위해 추가
from datetime import datetime # 날짜/시간 생성을 위해 추가
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFrame, QScrollArea, QGridLayout, 
    QComboBox, QMessageBox, QFileDialog, QSplitter, QTreeWidget, 
    QTreeWidgetItem, QButtonGroup, QRadioButton, QCheckBox, QAbstractItemView,
    QSizePolicy, QDialog, QTextEdit, QLayout
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QColor, QPalette, QIcon

# 기존 로직 모듈 임포트 (수정 없이 사용)
import config
from logic import TimetableLogic
from ai_mover import AIChainedMover

# --- 스타일 및 설정 ---
STYLE_SHEET = """
/* 시스템 다크모드 무시 및 라이트 테마 강제 적용 */
QWidget {
    background-color: #ffffff;
    color: #1f2937;
    font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
}

QMainWindow {
    background-color: #f3f4f6;
}

/* 라벨 스타일: 불필요한 여백 제거 */
QLabel {
    background-color: transparent;
    color: #1f2937;
    padding: 0px;
    margin: 0px;
}

/* 라디오 버튼 스타일 (개선됨: 마우스 오버 효과 추가) */
QRadioButton {
    background-color: transparent;
    color: #1f2937;
    font-weight: bold;
    spacing: 8px;
    padding: 6px 10px; /* 클릭 영역 확보 */
    border-radius: 6px; /* 둥근 모서리 */
}
QRadioButton:hover {
    background-color: #eff6ff; /* 마우스 오버 시 연한 파란색 배경 */
    color: #2563eb; /* 텍스트 색상 강조 */
}
QRadioButton:checked {
    background-color: #dbeafe; /* 선택 시 배경색 */
    color: #1d4ed8;
}
QRadioButton::indicator {
    width: 14px;
    height: 14px;
}

/* 모드 전환 탭 버튼 스타일 */
QPushButton#ModeBtn {
    background-color: #ffffff;
    color: #4b5563;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    padding: 10px 16px;
    font-weight: bold;
    font-size: 11px;
    text-align: center;
}
QPushButton#ModeBtn:hover {
    background-color: #f9fafb;
    border-color: #9ca3af;
}
QPushButton#ModeBtn:checked {
    background-color: #3b82f6;
    color: white;
    border: 1px solid #2563eb;
}

/* 일반 버튼 스타일 */
QPushButton {
    background-color: #ffffff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 6px 12px;
    color: #374151;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #f9fafb;
    border-color: #9ca3af;
}
QPushButton#PrimaryBtn {
    background-color: #3b82f6;
    color: white;
    border: 1px solid #2563eb;
}
QPushButton#PrimaryBtn:hover {
    background-color: #2563eb;
}
QPushButton#SuccessBtn {
    background-color: #10b981;
    color: white;
    border: 1px solid #059669;
}
QPushButton#SuccessBtn:hover {
    background-color: #059669;
}
QPushButton#DangerBtn {
    background-color: #ef4444;
    color: white;
    border: 1px solid #dc2626;
}
QPushButton#DangerBtn:hover {
    background-color: #dc2626;
}

QFrame#Card {
    background-color: white;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
}
QScrollArea {
    border: none;
    background-color: transparent;
}
/* 스크롤 영역 내부 위젯 배경 강제 지정 */
QScrollArea > QWidget > QWidget {
    background-color: #ffffff;
}

/* 트리 위젯 (로그창) */
QTreeWidget {
    border: 1px solid #e5e7eb;
    border-radius: 6px;
    background-color: white;
    color: #1f2937;
}
QTreeWidget::item {
    color: #1f2937;
    height: 24px;
}
QTreeWidget::item:selected {
    background-color: #3b82f6;
    color: white;
}
QHeaderView::section {
    background-color: #f9fafb;
    padding: 4px;
    border: 0px;
    font-weight: bold;
    color: #4b5563;
}
/* 콤보박스 스타일 */
QComboBox {
    background-color: white;
    color: #1f2937;
    border: 1px solid #d1d5db;
    border-radius: 4px;
    padding: 4px;
}
QComboBox QAbstractItemView {
    background-color: white;
    color: #1f2937;
    selection-background-color: #3b82f6;
}

/* 셀 프레임 자체의 패딩 제거 */
QFrame#Cell {
    padding: 0px;
    margin: 0px;
}
"""

COLORS = {
    "cell_default": "#f9fafb",
    "cell_locked": "#e5e7eb",
    "cell_changed": "#fef9c3",
    "cell_selected": "#dbeafe",
    "cell_target": "#dcfce7",
    "cell_conflict": "#fee2e2",
    "cell_chain_src": "#f3e8ff",
    "cell_chain_tgt": "#e9d5ff",
    "text_primary": "#111827",
    "text_secondary": "#6b7280",
    "accent": "#3b82f6"
}

class HelpDialog(QDialog):
    """도움말 팝업창"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("사용법 안내")
        self.resize(600, 500)
        self.setStyleSheet("background-color: white; color: #333333;")
        
        layout = QVBoxLayout(self)
        
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setFrameShape(QFrame.Shape.NoFrame)
        text_edit.setStyleSheet("font-family: 'Malgun Gothic'; font-size: 11pt; color: #333333; background-color: white;")
        
        help_content = """
<h2>📖 스마트 시간표 매니저 사용법</h2>
<hr>
<h3>1. 기본 기능</h3>
<ul>
    <li><b>불러오기:</b> CSV 형식의 시간표 파일을 불러옵니다.</li>
    <li><b>저장:</b> 작업한 내용을 CSV 파일로 저장합니다.</li>
    <li><b>실행취소:</b> 방금 수행한 작업을 되돌립니다 (Undo).</li>
    <li><b>선택해제:</b> 현재 선택된 셀이나 작업을 취소합니다 (ESC 키).</li>
</ul>

<h3>2. 작업 모드 (상단 버튼)</h3>
<ul>
    <li><b>👁️ 조회 모드:</b> 수업을 클릭하면 해당 교사의 주간 일정이 강조됩니다. 우클릭 시 '잠금' 설정이 가능합니다.</li>
    <li><b>🔄 맞교환 모드:</b> 바꿀 두 개의 수업을 차례로 클릭하여 서로 위치를 바꿉니다.</li>
    <li><b>🛠️ 보강 모드:</b> 결강이 생긴 수업을 클릭하고 대체 교사를 배정합니다.</li>
    <li><b>🔗 연쇄 이동 모드:</b> 수업을 하나 선택해 다른 자리로 옮깁니다. 기존에 있던 수업은 밀려나게 되며, 이를 반복하여 정리할 수 있습니다.</li>
    <li><b>🤖 AI 자동 모드:</b> 수업을 옮길 때, 밀려나는 수업들의 자리를 AI가 자동으로 찾아줍니다.</li>
</ul>

<h3>3. 보기 방식</h3>
<ul>
    <li><b>교과별 조회:</b> '도덕', '도A', '도덕A' 등 유사한 교과는 <b>대표 교과(도덕)</b> 하나로 묶여 메뉴에 표시됩니다. 선택 시 모든 유사 교과가 함께 출력됩니다.</li>
</ul>

<h3>4. 팁 (Tip)</h3>
<ul>
    <li><b>로그 접기/펼치기:</b> 중앙 '변경 내역' 헤더의 버튼을 눌러 로그 창을 최소화하고 시간표를 넓게 볼 수 있습니다.</li>
    <li><b>우클릭:</b> 셀을 잠그거나 해제할 수 있습니다.</li>
</ul>

<br>
<hr>
<p style='font-size:10pt; color:#666666;'>
■ 개발자 정보<br>
- 개발일: 2026.01.20<br>
- ✉: trsketch@gmail.com<br>
- 무단 배포 및 상업적 사용 금지<br>
<b>© Copyright 2026. All rights reserved.</b>
</p>
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

class TimetableWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Timetable Manager Pro")
        self.resize(1400, 950)
        
        self.force_light_palette()
        self.setStyleSheet(STYLE_SHEET)

        # 로직 초기화
        self.logic = TimetableLogic()
        self.ai_mover = AIChainedMover(self.logic)

        # 상태 변수
        self.view_mode = "ALL_WEEK"
        self.work_mode = "VIEW"
        self.use_ai_mode = False
        
        self.swap_source = None
        self.swap_candidates = []
        self.highlighted_teachers = {}
        self.selected_cell_info = None
        self.last_swapped_cells = []
        
        self.chain_floating_data = None
        
        # 셀 위젯 관리 맵
        self.cell_widget_map = {}

        self.init_ui()

    def force_light_palette(self):
        """시스템 다크모드를 무시하고 밝은 색상 테마를 강제 적용"""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(31, 41, 55)) # #1f2937
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(249, 250, 251))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(31, 41, 55))
        palette.setColor(QPalette.ColorRole.Text, QColor(31, 41, 55))
        palette.setColor(QPalette.ColorRole.Button, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(31, 41, 55))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, QColor(59, 130, 246))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(59, 130, 246))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        self.setPalette(palette)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)

        # 1. 상단 컨트롤 패널 (Card)
        top_panel = QFrame()
        top_panel.setObjectName("Card")
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(15, 15, 15, 15)

        # [좌측] 버튼 그룹
        btn_group_layout = QHBoxLayout()
        self.btn_load = QPushButton("📂 불러오기")
        self.btn_load.clicked.connect(self.load_csv)
        self.btn_save = QPushButton("💾 저장")
        self.btn_save.clicked.connect(self.save_csv)
        self.btn_save.setObjectName("SuccessBtn")
        self.btn_undo = QPushButton("↩ 실행취소")
        self.btn_undo.clicked.connect(self.undo_action)
        self.btn_cancel = QPushButton("🚫 선택해제")
        self.btn_cancel.clicked.connect(self.cancel_action)
        self.btn_cancel.setObjectName("DangerBtn")
        
        btn_group_layout.addWidget(self.btn_load)
        btn_group_layout.addWidget(self.btn_save)
        btn_group_layout.addWidget(self.btn_undo)
        btn_group_layout.addWidget(self.btn_cancel)
        
        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.VLine)
        line1.setFrameShadow(QFrame.Shadow.Sunken)
        line1.setStyleSheet("color: #e5e7eb;")

        # [중앙] 모드 탭 버튼
        mode_group_layout = QHBoxLayout()
        mode_group_layout.setSpacing(5)
        
        self.mode_btn_group = QButtonGroup(self)
        self.mode_btn_group.setExclusive(True)
        self.mode_btn_group.buttonClicked.connect(self.on_mode_change)

        modes = [
            ("👁️ 조회모드", "VIEW", False),
            ("🔄 맞교환모드", "SWAP", False),
            ("🛠️ 보강모드", "COVER", False),
            ("🔗 연쇄 이동 모드", "CHAIN", False),
            ("🤖 AI 자동 모드", "CHAIN", True)
        ]
        
        for text, val, use_ai in modes:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setObjectName("ModeBtn")
            btn.setProperty("mode_val", val)
            btn.setProperty("use_ai", use_ai)
            if val == "VIEW": btn.setChecked(True)
            self.mode_btn_group.addButton(btn)
            mode_group_layout.addWidget(btn)

        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.VLine)
        line2.setStyleSheet("color: #e5e7eb;")

        # [우측] 컨텍스트 옵션
        self.context_stack = QWidget()
        self.context_layout = QHBoxLayout(self.context_stack)
        self.context_layout.setContentsMargins(0, 0, 0, 0)
        
        self.cover_widget = QWidget()
        cover_layout = QHBoxLayout(self.cover_widget)
        cover_layout.setContentsMargins(0, 0, 0, 0)
        cover_layout.addWidget(QLabel("대체 교사:"))
        self.combo_cover_teacher = QComboBox()
        self.combo_cover_teacher.setMinimumWidth(120)
        btn_apply_cover = QPushButton("배정")
        btn_apply_cover.clicked.connect(self.execute_cover)
        btn_apply_cover.setObjectName("PrimaryBtn")
        cover_layout.addWidget(self.combo_cover_teacher)
        cover_layout.addWidget(btn_apply_cover)
        self.cover_widget.setVisible(False)
        self.context_layout.addWidget(self.cover_widget)

        top_layout.addLayout(btn_group_layout)
        top_layout.addSpacing(15)
        top_layout.addWidget(line1)
        top_layout.addSpacing(15)
        top_layout.addLayout(mode_group_layout)
        top_layout.addSpacing(15)
        top_layout.addWidget(line2)
        top_layout.addSpacing(15)
        top_layout.addWidget(self.context_stack)
        top_layout.addStretch()
        
        btn_reset = QPushButton("초기화")
        btn_reset.clicked.connect(self.reset_all)
        top_layout.addWidget(btn_reset)
        
        btn_help = QPushButton("❓ 도움말")
        btn_help.clicked.connect(self.show_help)
        top_layout.addWidget(btn_help)

        main_layout.addWidget(top_panel)

        # 2. 메인 콘텐츠 (Splitter)
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 로그 창
        self.log_group = QFrame()
        self.log_group.setObjectName("Card")
        log_layout = QVBoxLayout(self.log_group)
        log_layout.setContentsMargins(0, 0, 0, 0)
        
        # 로그창 헤더에 접기/펼치기 버튼 추가를 위한 컨테이너 구성
        log_header_container = QWidget()
        log_header_container.setFixedHeight(40)
        log_header_container.setStyleSheet("background-color: #f9fafb; border-bottom: 1px solid #e5e7eb; border-top-left-radius: 8px; border-top-right-radius: 8px;")
        header_layout = QHBoxLayout(log_header_container)
        header_layout.setContentsMargins(10, 0, 10, 0)
        
        lbl_title = QLabel("📋 변경 내역")
        lbl_title.setStyleSheet("font-weight: bold; color: #1f2937; border: none;")
        
        self.btn_toggle_log = QPushButton("접기 ▲")
        self.btn_toggle_log.setFixedSize(80, 24)
        self.btn_toggle_log.setStyleSheet("""
            QPushButton { background-color: white; border: 1px solid #d1d5db; border-radius: 4px; font-size: 11px; }
            QPushButton:hover { background-color: #f3f4f6; }
        """)
        self.btn_toggle_log.clicked.connect(self.toggle_log_view)

        header_layout.addWidget(lbl_title)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_toggle_log)
        
        log_layout.addWidget(log_header_container)

        # 로그 내용 박스 (트리 위젯 포함) - 접기/펼치기 대상
        self.log_content_box = QWidget()
        log_content_layout = QHBoxLayout(self.log_content_box)
        self.tree_left = self.create_log_tree()
        self.tree_right = self.create_log_tree()
        log_content_layout.addWidget(self.tree_left)
        log_content_layout.addWidget(self.tree_right)
        log_layout.addWidget(self.log_content_box)
        
        self.splitter.addWidget(self.log_group)

        # 그리드 창
        grid_group = QFrame()
        grid_group.setObjectName("Card")
        grid_group_layout = QVBoxLayout(grid_group)
        grid_group_layout.setContentsMargins(0, 0, 0, 0)

        option_bar = QFrame()
        option_bar.setStyleSheet("background-color: #f9fafb; border-bottom: 1px solid #e5e7eb;")
        option_layout = QHBoxLayout(option_bar)
        option_layout.addWidget(QLabel("보기 방식:"))
        
        self.view_btn_group = QButtonGroup(self) # [수정] 오타 수정: QButtonGroup(self.view_btn_group) -> QButtonGroup(self)
        self.view_btn_group.buttonClicked.connect(self.on_view_change)
        view_modes = [("주간 전체", "ALL_WEEK"), ("요일별", "ALL_DAY"), ("학급별", "SINGLE"), ("교사별", "TEACHER"), ("교과별", "SUBJECT")]
        for text, val in view_modes:
            rb = QRadioButton(text)
            rb.setProperty("view_val", val)
            if val == "ALL_WEEK": rb.setChecked(True)
            self.view_btn_group.addButton(rb)
            option_layout.addWidget(rb)
        
        option_layout.addSpacing(20)
        self.selector_stack = QWidget()
        self.selector_layout = QHBoxLayout(self.selector_stack)
        self.selector_layout.setContentsMargins(0, 0, 0, 0)
        option_layout.addWidget(self.selector_stack)
        option_layout.addStretch()

        grid_group_layout.addWidget(option_bar)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        # 초기 컨테이너
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.scroll_area.setWidget(self.grid_container)
        
        grid_group_layout.addWidget(self.scroll_area)
        
        self.status_bar = QLabel(" 파일을 불러와주세요.")
        self.status_bar.setFixedHeight(30)
        self.status_bar.setStyleSheet("background-color: #ffffff; color: #3b82f6; font-weight: bold; padding-left: 10px;")
        grid_group_layout.addWidget(self.status_bar)

        self.splitter.addWidget(grid_group)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 4)
        main_layout.addWidget(self.splitter)

    def create_log_tree(self):
        tree = QTreeWidget()
        tree.setHeaderLabels(["구분", "학반", "내용"])
        tree.header().resizeSection(0, 60)
        tree.header().resizeSection(1, 70)
        tree.setIndentation(0)
        tree.setAlternatingRowColors(True)
        tree.setStyleSheet("color: #1f2937;")
        return tree
    
    # 로그 창 접기/펼치기 슬롯 함수
    def toggle_log_view(self):
        visible = self.log_content_box.isVisible()
        self.log_content_box.setVisible(not visible)
        
        if visible: # 현재 보임 -> 숨김 (접기)
            self.btn_toggle_log.setText("펼치기 ▼")
            self.log_group.setMaximumHeight(45) # 헤더 높이만큼 고정하여 공간 확보 방지
            
            # Splitter 크기 재조정 (로그창 최소화, 나머지 그리드 확장)
            total_height = self.splitter.height()
            # 45px은 헤더 높이 + 보더 여유분
            self.splitter.setSizes([45, total_height - 45])
            
        else: # 현재 숨김 -> 보임 (펼치기)
            self.btn_toggle_log.setText("접기 ▲")
            self.log_group.setMaximumHeight(16777215) # 최대 높이 제한 해제
            
            # 비율 복구 (예: 로그 2 : 그리드 8)
            total_height = self.splitter.height()
            self.splitter.setSizes([int(total_height * 0.2), int(total_height * 0.8)])

    # --- 기능 구현 ---
    def show_help(self):
        HelpDialog(self).exec()

    def load_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "CSV 파일 열기", "", "CSV Files (*.csv)")
        if not file_path: return
        success, msg = self.logic.import_school_csv(file_path)
        if success:
            self.status_bar.setText(f"✅ {msg}")
            self.status_bar.setStyleSheet("color: #10b981; font-weight: bold; padding-left: 10px;")
            self.view_mode = "ALL_WEEK"
            self.refresh_selectors()
            self.refresh_grid()
            self.update_log_view()
        else:
            QMessageBox.critical(self, "오류", msg)

    def save_csv(self):
        if not self.logic.schedule: return
        
        # 현재 날짜와 시간을 이용해 파일명 생성 (예: timetable-260121101420.csv)
        current_time = datetime.now().strftime("%y%m%d%H%M%S")
        default_filename = f"timetable-{current_time}.csv"
        
        file_path, _ = QFileDialog.getSaveFileName(self, "CSV 파일 저장", default_filename, "CSV Files (*.csv)")
        if not file_path: return
        success, msg = self.logic.export_csv(file_path)
        if success:
            self.status_bar.setText(f"💾 {msg}")
            QMessageBox.information(self, "완료", msg)
        else:
            QMessageBox.critical(self, "오류", msg)

    def undo_action(self):
        self.cancel_action()
        if self.logic.undo():
            self.update_cell_visuals()
            self.update_log_view()
            self.status_bar.setText("↩ 실행 취소 완료")
        else:
            self.status_bar.setText("⚠️ 더 이상 취소할 작업이 없습니다.")

    def cancel_action(self):
        self.swap_source = None
        self.swap_candidates = []
        self.selected_cell_info = None
        self.highlighted_teachers = {}
        if self.work_mode == "CHAIN" and self.chain_floating_data:
            data = self.chain_floating_data
            g, c = data['origin_gc']
            d, p = data['origin_time']
            if not self.logic.schedule[g][c][d].get(p):
                self.logic.add_class(g, c, d, p, data['subject'], data['teacher'])
            self.chain_floating_data = None
        self.combo_cover_teacher.clear()
        self.status_bar.setText("선택이 취소되었습니다.")
        self.update_cell_visuals()

    def reset_all(self):
        if not self.logic.original_schedule: return
        res = QMessageBox.question(self, "전체 초기화", "모든 변경 사항을 취소하시겠습니까?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if res == QMessageBox.StandardButton.Yes:
            if self.logic.restore_original_state():
                self.cancel_action()
                self.refresh_grid()
                self.update_log_view()
                self.status_bar.setText("🔄 초기화 완료")

    def on_mode_change(self, btn):
        self.cancel_action()
        self.work_mode = btn.property("mode_val")
        self.use_ai_mode = btn.property("use_ai")
        self.cover_widget.setVisible(False)
        msg = ""
        if self.work_mode == "VIEW": msg = "[조회 모드] 수업 클릭 시 교사 일정 강조. 우클릭 시 잠금."
        elif self.work_mode == "SWAP": msg = "[맞교환 모드] 바꿀 두 수업을 순서대로 클릭."
        elif self.work_mode == "COVER":
            msg = "[보강 모드] 보강할 수업 선택."
            self.cover_widget.setVisible(True)
        elif self.work_mode == "CHAIN":
            msg = "[AI 자동 모드] 이동 시 연쇄 충돌 자동 해결." if self.use_ai_mode else "[연쇄 이동 모드] 수동으로 밀어내기 이동."
        self.status_bar.setText(msg)
        self.status_bar.setStyleSheet(f"color: {COLORS['accent']}; font-weight: bold; padding-left: 10px;")
        self.update_cell_visuals()

    def on_view_change(self, btn):
        self.view_mode = btn.property("view_val")
        self.refresh_selectors()
        self.refresh_grid()

    # --- 그리드 렌더링 ---

    def refresh_selectors(self):
        for i in reversed(range(self.selector_layout.count())): 
            self.selector_layout.itemAt(i).widget().setParent(None)
        if self.view_mode == "ALL_DAY":
            self.selector_layout.addWidget(QLabel("요일:"))
            self.combo_sel = QComboBox()
            self.combo_sel.addItems(config.DAYS)
            self.combo_sel.currentTextChanged.connect(self.refresh_grid)
            self.selector_layout.addWidget(self.combo_sel)
        elif self.view_mode == "SINGLE":
            self.selector_layout.addWidget(QLabel("학급:"))
            self.combo_sel = QComboBox()
            
            classes = self.logic.get_all_sorted_classes()
            self.combo_sel.addItems([f"{g}-{c}" for g, c in classes])
            
            # [수정] 아이템 폭 계산하여 자동 조절
            self.adjust_combo_width(self.combo_sel)
            
            self.combo_sel.currentTextChanged.connect(self.refresh_grid)
            self.selector_layout.addWidget(self.combo_sel)
        elif self.view_mode == "TEACHER":
            self.selector_layout.addWidget(QLabel("교사:"))
            self.combo_sel = QComboBox()
            
            teachers = self.logic.get_all_teachers_sorted()
            self.combo_sel.addItems(teachers)
            
            # [수정] 아이템 폭 계산하여 자동 조절
            self.adjust_combo_width(self.combo_sel)
            
            self.combo_sel.currentTextChanged.connect(self.refresh_grid)
            self.selector_layout.addWidget(self.combo_sel)
        elif self.view_mode == "SUBJECT":
            self.selector_layout.addWidget(QLabel("교과:"))
            self.combo_sel = QComboBox()
            
            # 1. 모든 교과목 수집
            all_subjects = set()
            if self.logic.schedule:
                for g_data in self.logic.schedule.values():
                    for c_data in g_data.values():
                        for day_data in c_data.values():
                            for info in day_data.values():
                                if info and 'subject' in info:
                                    all_subjects.add(info['subject'])
            
            # 2. 교과목 그룹화 (대표 교과 선정)
            # 정렬 기준: 
            # (1) 순수 한글(알파벳/숫자 미포함) 우선
            # (2) 길이가 짧은 순
            # (3) 가나다 순
            def subject_sort_key(s):
                has_alnum = any(c.isascii() and c.isalnum() for c in s)
                return (has_alnum, len(s), s)

            sorted_subjects = sorted(list(all_subjects), key=subject_sort_key)
            representatives = []

            for subj in sorted_subjects:
                is_covered = False
                for rep in representatives:
                    # 이미 등록된 대표 교과와 유사하면(포함되거나 변형된 형태면) 추가하지 않음
                    if self.is_subject_similar(rep, subj):
                        is_covered = True
                        break
                if not is_covered:
                    representatives.append(subj)
            
            # 3. 대표 교과만 메뉴에 추가 (가나다순 정렬)
            representatives.sort()
            self.combo_sel.addItems(representatives)

            self.adjust_combo_width(self.combo_sel)
            self.combo_sel.currentTextChanged.connect(self.refresh_grid)
            self.selector_layout.addWidget(self.combo_sel)

    def adjust_combo_width(self, combo):
        """콤보박스 아이템의 텍스트 길이에 맞춰 폭을 자동 조절"""
        width = 0
        fm = combo.fontMetrics()
        for i in range(combo.count()):
            w = fm.horizontalAdvance(combo.itemText(i))
            if w > width:
                width = w
        # 텍스트 폭 + 아이콘/패딩 여유분(40px)
        combo.setMinimumWidth(width + 40)

    def refresh_grid(self, _=None):
        """GridLayout 정렬 문제 해결 (VBox + Stretch 사용)"""
        old_widget = self.scroll_area.widget()
        if old_widget: old_widget.deleteLater()
            
        self.grid_container = QWidget()
        main_vbox = QVBoxLayout(self.grid_container)
        main_vbox.setContentsMargins(0, 0, 0, 0)
        main_vbox.setSpacing(0)
        
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(1)
        self.grid_layout.setContentsMargins(1, 1, 1, 1)
        
        main_vbox.addLayout(self.grid_layout)
        main_vbox.addStretch(1) # 남은 공간을 모두 차지하여 그리드를 위로 밀어올림
        
        self.scroll_area.setWidget(self.grid_container)
        
        self.cell_widget_map.clear()
        
        if self.view_mode == "ALL_WEEK": self.render_all_week()
        elif self.view_mode == "ALL_DAY": self.render_all_day()
        elif self.view_mode == "SINGLE": self.render_single()
        elif self.view_mode == "TEACHER": self.render_teacher()
        elif self.view_mode == "SUBJECT": self.render_subject()

    def update_cell_visuals(self):
        for key, cell_widget in self.cell_widget_map.items():
            self._update_single_cell(cell_widget, key)

    def _update_single_cell(self, cell, key):
        grade, cls, day, period = key
        grade, cls = str(grade), str(cls)
        period = int(period)
        data = self.logic.schedule[grade][cls][day].get(period)
        
        main_text, sub_text = "", ""
        teacher_name = data['teacher'] if data else None

        if data:
            if self.view_mode == "TEACHER":
                main_text, sub_text = data['subject'], f"{grade}-{cls}"
            elif self.view_mode == "ALL_DAY":
                main_text = f"{data['subject']} ({teacher_name})"
            else:
                main_text, sub_text = data['subject'], teacher_name

        bg_color = COLORS["cell_default"]
        border_color = "#e5e7eb"
        border_width = 1
        text_color = "#1f2937" # 기본 검정색

        if self.logic.is_locked(grade, cls, day, period):
            bg_color = COLORS["cell_locked"]
            main_text = "🔒 " + main_text
        if self.logic.is_changed(grade, cls, day, period):
            bg_color = COLORS["cell_changed"]

        # [복원] 중복 교사(Conflict) 체크: 같은 시간대에 해당 교사가 2개 이상의 수업을 하는지 확인
        if teacher_name:
            t_sched = self.logic.teachers_schedule.get(teacher_name, {})
            if day in t_sched and period in t_sched[day]:
                if len(t_sched[day][period]) > 1:
                    bg_color = COLORS["cell_conflict"] # 상시 붉은 배경

        if self.swap_source == key:
            bg_color = COLORS["cell_selected"]
            border_color, border_width = COLORS["accent"], 2
        elif self.work_mode == "SWAP" and self.swap_source:
             src_g, src_c, _, _ = self.swap_source
             if (grade, cls) == (src_g, src_c) and (day, period) in self.swap_candidates:
                 bg_color = COLORS["cell_target"]
                 border_color = "#10b981"
        elif self.work_mode == "COVER" and self.selected_cell_info == key:
            bg_color = COLORS["cell_conflict"]
            border_color, border_width = "#ef4444", 2
        elif self.work_mode == "CHAIN" and self.chain_floating_data:
            orig_g, orig_c = self.chain_floating_data['origin_gc']
            orig_d, orig_p = self.chain_floating_data['origin_time']
            floater = self.chain_floating_data['teacher']
            if key == (str(orig_g), str(orig_c), orig_d, orig_p):
                bg_color = COLORS["cell_chain_tgt"]
            elif (grade, cls) == (str(orig_g), str(orig_c)):
                 if not self.logic.is_locked(grade, cls, day, period):
                     if self.logic.is_teacher_busy(floater, day, period):
                         bg_color = COLORS["cell_conflict"]
                     else:
                         bg_color = COLORS["cell_target"]
            if teacher_name == floater:
                bg_color = COLORS["cell_chain_src"]

        if teacher_name and teacher_name in self.highlighted_teachers:
             # 중복 배경색도 선택 시에는 하이라이트 색으로 덮어씀
             if bg_color in [COLORS["cell_default"], COLORS["cell_locked"], COLORS["cell_changed"], COLORS["cell_conflict"]]:
                 bg_color = self.highlighted_teachers[teacher_name]
                 if bg_color == COLORS["cell_selected"]: border_color = COLORS["accent"]

        # [수정] 3연강 이상 교사는 보라색 글자로 표시
        if teacher_name and self.is_consecutive_3(teacher_name, day, period):
             text_color = "#9333ea" # 보라색

        cell.set_content(main_text, sub_text, bg_color, border_color, border_width, text_color)

    def add_header(self, text, r, c, rowspan=1, colspan=1):
        lbl = QLabel(text)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("background-color: #e5e7eb; font-weight: bold; border: 1px solid #d1d5db; color: #1f2937;")
        # [수정] 헤더 높이 축소 (35 -> 30)
        lbl.setMinimumHeight(30)
        if len(text) > 4: lbl.setMinimumWidth(80) 
        else: lbl.setMinimumWidth(40)
        self.grid_layout.addWidget(lbl, r, c, rowspan, colspan)

    def add_cell(self, grade, cls, day, period, r, c, rowspan=1, colspan=1):
        key = (str(grade), str(cls), day, int(period))
        cell = ClickableFrame(key)
        self._update_single_cell(cell, key)
        cell.clicked.connect(self.handle_cell_click)
        cell.right_clicked.connect(self.handle_right_click)
        self.grid_layout.addWidget(cell, r, c, rowspan, colspan)
        self.cell_widget_map[key] = cell

    def is_consecutive_3(self, teacher, day, period):
        return self.logic.check_consecutive_classes(teacher, day, period)
    
    # 유사 교과 판별 로직
    def is_subject_similar(self, target, selected):
        """
        두 교과명이 유사한지 판단합니다.
        1. 정확히 일치
        2. 한쪽이 다른 쪽에 포함됨 (예: '도덕' in '도덕A')
        3. 첫 글자가 같고, 한쪽에 영문/숫자가 포함된 경우 (약어 패턴, 예: '도덕' vs '도A')
        """
        if not target or not selected: return False
        
        # 공백 제거 후 비교
        t = target.replace(" ", "")
        s = selected.replace(" ", "")
        
        if t == s: return True
        if s in t or t in s: return True
        
        # 약어 패턴 확인: 첫 글자가 같고, 영문/숫자가 포함되어 있으면 유사한 것으로 간주
        if t[0] == s[0]:
            # 영문 또는 숫자가 포함되어 있는지 확인
            has_extra_t = any(c.isascii() and c.isalnum() for c in t)
            has_extra_s = any(c.isascii() and c.isalnum() for c in s)
            if has_extra_t or has_extra_s:
                return True
                
        return False

    # --- 핸들러 ---
    def handle_cell_click(self, key):
        grade, cls, day, period = key
        grade, cls = str(grade), str(cls)
        cell_data = self.logic.schedule[grade][cls][day].get(period)
        clicked_teacher = cell_data['teacher'] if cell_data else None

        if clicked_teacher: self.highlighted_teachers = {clicked_teacher: COLORS["cell_selected"]}
        else: self.highlighted_teachers = {}

        if self.work_mode == "VIEW":
            is_locked = "🔒 " if self.logic.is_locked(grade, cls, day, period) else ""
            msg = f"{is_locked}선택: {clicked_teacher} ({cell_data['subject']})" if clicked_teacher else "빈 교시"
            self.status_bar.setText(msg)
        elif self.work_mode == "SWAP":
            if self.logic.is_locked(grade, cls, day, period):
                self.status_bar.setText("🔒 잠긴 수업입니다.")
                return
            if not self.swap_source:
                if not cell_data:
                    self.status_bar.setText("⚠️ 빈 교시는 선택할 수 없습니다.")
                    return
                self.swap_source = key
                self.swap_candidates = self.logic.get_swap_candidates(grade, cls, day, period)
                self.status_bar.setText(f"1단계: {clicked_teacher}. 이동할 위치(초록색)를 선택하세요.")
            else:
                src_g, src_c, src_d, src_p = self.swap_source
                if key == self.swap_source:
                    self.cancel_action()
                    return
                if (grade, cls) != (src_g, src_c):
                    QMessageBox.warning(self, "오류", "같은 반 내에서만 교환 가능합니다.")
                    return
                if self.logic.is_locked(grade, cls, day, period):
                    QMessageBox.warning(self, "오류", "목표 대상이 잠겨있습니다.")
                    return
                self.logic.execute_swap(grade, cls, src_d, src_p, day, period)
                self.last_swapped_cells = [self.swap_source, key]
                self.swap_source = None
                self.swap_candidates = []
                self.status_bar.setText("✅ 교체 완료")
                self.update_log_view()
        elif self.work_mode == "COVER":
            if not cell_data: return
            if self.logic.is_locked(grade, cls, day, period):
                self.status_bar.setText("🔒 잠긴 수업입니다.")
                return
            self.selected_cell_info = key
            self.highlighted_teachers = {clicked_teacher: COLORS["cell_conflict"]}
            candidates = self.logic.get_cover_candidates(day, period)
            self.combo_cover_teacher.clear()
            if candidates:
                self.combo_cover_teacher.addItems(candidates)
                self.status_bar.setText(f"대상: {clicked_teacher}. 대체 교사를 선택하고 배정 버튼을 누르세요.")
            else:
                self.status_bar.setText("⚠️ 추천 가능한 교사가 없습니다.")
        elif self.work_mode == "CHAIN":
            if self.logic.is_locked(grade, cls, day, period): return
            if self.use_ai_mode:
                if not self.chain_floating_data:
                    if not cell_data: return
                    self.chain_floating_data = cell_data.copy()
                    self.chain_floating_data['origin_gc'] = (grade, cls)
                    self.chain_floating_data['origin_time'] = (day, period)
                    self.highlighted_teachers = {clicked_teacher: COLORS["cell_chain_src"]}
                    self.status_bar.setText(f"🤖 [AI] {clicked_teacher} 교사가 이동할 목표 위치를 클릭하세요.")
                else:
                    orig_g, orig_c = self.chain_floating_data['origin_gc']
                    orig_d, orig_p = self.chain_floating_data['origin_time']
                    if (grade, cls) != (orig_g, orig_c):
                        QMessageBox.warning(self, "오류", "같은 반 내에서 이동해야 합니다.")
                        return
                    success, msg, logs = self.ai_mover.try_ai_move(orig_g, orig_c, orig_d, orig_p, day, period)
                    if success: self.status_bar.setText(f"✅ {msg}")
                    else:
                        QMessageBox.warning(self, "AI 실패", msg)
                        self.status_bar.setText("AI 이동 실패")
                    self.chain_floating_data = None
                    self.update_log_view()
            else:
                if not self.chain_floating_data:
                    if not cell_data: return
                    self.logic.save_snapshot()
                    self.chain_floating_data = cell_data.copy()
                    self.chain_floating_data['origin_gc'] = (grade, cls)
                    self.chain_floating_data['origin_time'] = (day, period)
                    self.logic.remove_class(grade, cls, day, period)
                    self.highlighted_teachers = {clicked_teacher: COLORS["cell_chain_src"]}
                    self.status_bar.setText(f"🚀 [이동 중] {clicked_teacher}. 어디에 놓으시겠습니까?")
                else:
                    orig_g, orig_c = self.chain_floating_data['origin_gc']
                    if (grade, cls) != (orig_g, orig_c): return
                    floater = self.chain_floating_data
                    target_old_data = self.logic.schedule[grade][cls][day].get(period)
                    self.logic.save_snapshot()
                    self.logic.add_class(grade, cls, day, period, floater['subject'], floater['teacher'])
                    self.logic.change_logs.append({
                        "type": "연쇄", "class": f"{grade}-{cls}",
                        "desc": f"{floater['teacher']} → {day}{period} 이동",
                        "log_key": ("CHAIN", grade, cls, day, period)
                    })
                    if target_old_data:
                        self.chain_floating_data = target_old_data.copy()
                        self.chain_floating_data['origin_gc'] = (grade, cls)
                        self.chain_floating_data['origin_time'] = (day, period)
                        self.highlighted_teachers = {target_old_data['teacher']: COLORS["cell_chain_src"]}
                        self.status_bar.setText(f"🔄 [밀림] {target_old_data['teacher']} 교사를 다시 배치하세요.")
                    else:
                        self.chain_floating_data = None
                        self.status_bar.setText("✅ 이동 완료")
                    self.update_log_view()
        self.update_cell_visuals()

    def handle_right_click(self, key):
        grade, cls, day, period = key
        is_locked = self.logic.toggle_lock(grade, cls, day, period)
        msg = "🔒 잠금 설정" if is_locked else "🔓 잠금 해제"
        self.status_bar.setText(f"[{grade}-{cls} {day}{period}] {msg}")
        self.update_cell_visuals()

    def execute_cover(self):
        if not self.selected_cell_info: return
        new_teacher = self.combo_cover_teacher.currentText()
        if not new_teacher: return
        g, c, d, p = self.selected_cell_info
        self.logic.update_teacher(g, c, d, p, new_teacher)
        self.selected_cell_info = None
        self.combo_cover_teacher.clear()
        self.status_bar.setText(f"✅ 보강 완료: {new_teacher}")
        self.update_log_view()
        self.update_cell_visuals()

    def update_log_view(self):
        self.tree_left.clear()
        self.tree_right.clear()
        
        if hasattr(self.logic, 'get_diff_list'):
            logs = self.logic.get_diff_list()
        else:
            logs = self.logic.change_logs
            
        mid = (len(logs) + 1) // 2
        for i, log in enumerate(logs):
            if isinstance(log, dict):
                item = QTreeWidgetItem([str(log.get('type','')), str(log.get('class','')), str(log.get('desc',''))])
                if i < mid: self.tree_left.addTopLevelItem(item)
                else: self.tree_right.addTopLevelItem(item)
                if i == len(logs) - 1:
                    target = self.tree_right if i >= mid else self.tree_left
                    target.scrollToItem(item)

    # --- 렌더링 함수 ---
    
    def render_all_week(self):
        self.add_header("학반", 0, 0)
        self.grid_layout.setColumnMinimumWidth(0, 80)
        
        # [수정] 학급 수를 먼저 계산하여 세로선(요일 구분선)의 길이를 동적으로 지정
        classes = self.logic.get_all_sorted_classes()
        total_rows = len(classes) + 1  # 헤더(1줄) + 학급 데이터 줄 수

        col = 1
        for day in config.DAYS:
            limit = config.PERIODS_PER_DAY[day]
            for p in range(1, limit + 1):
                self.add_header(f"{day}{p}", 0, col)
                col += 1
            if day != config.DAYS[-1]:
                lbl = QLabel()
                lbl.setFixedWidth(5)
                lbl.setStyleSheet("background-color: #d1d5db;")
                # [수정] 불필요한 스크롤 방지를 위해 rowspan을 전체 행 개수에 맞춤 (기존 1000 -> total_rows)
                self.grid_layout.addWidget(lbl, 0, col, total_rows, 1)
                col += 1
        
        for r, (g, c) in enumerate(classes):
            row = r + 1
            self.add_header(f"{g}-{c}", row, 0)
            col = 1
            for day in config.DAYS:
                limit = config.PERIODS_PER_DAY[day]
                for p in range(1, limit + 1):
                    self.add_cell(g, c, day, p, row, col)
                    col += 1
                if day != config.DAYS[-1]: col += 1

    def render_all_day(self):
        if not hasattr(self, 'combo_sel'): return
        target_day = self.combo_sel.currentText()
        if not target_day: return
        self.add_header("학반", 0, 0)
        self.grid_layout.setColumnMinimumWidth(0, 80)
        limit = config.PERIODS_PER_DAY[target_day]
        for p in range(1, limit + 1):
            self.add_header(f"{p}교시", 0, p)
            self.grid_layout.setColumnStretch(p, 1)
        classes = self.logic.get_all_sorted_classes()
        for r, (g, c) in enumerate(classes):
            row = r + 1
            self.add_header(f"{g}-{c}", row, 0)
            for p in range(1, limit + 1):
                self.add_cell(g, c, target_day, p, row, p)

    def render_single(self):
        if not hasattr(self, 'combo_sel'): return
        cls_str = self.combo_sel.currentText()
        if not cls_str: return
        try: g, c = cls_str.split('-')
        except: return
        self.add_header("교시", 0, 0)
        for i, day in enumerate(config.DAYS):
            self.add_header(day, 0, i+1)
            self.grid_layout.setColumnStretch(i+1, 1)
            self.grid_layout.setColumnMinimumWidth(i+1, 120)
        for p in range(1, config.MAX_PERIODS + 1):
            self.add_header(f"{p}교시", p, 0)
            for i, day in enumerate(config.DAYS):
                if p <= config.PERIODS_PER_DAY[day]:
                    self.add_cell(g, c, day, p, p, i+1)

    def render_teacher(self):
        if not hasattr(self, 'combo_sel'): return
        t_name = self.combo_sel.currentText()
        if not t_name: return
        self.add_header("교시", 0, 0)
        for i, day in enumerate(config.DAYS):
            self.add_header(day, 0, i+1)
            self.grid_layout.setColumnStretch(i+1, 1)
            self.grid_layout.setColumnMinimumWidth(i+1, 120)
        for p in range(1, config.MAX_PERIODS + 1):
            self.add_header(f"{p}교시", p, 0)
            for i, day in enumerate(config.DAYS):
                found = False
                if t_name in self.logic.teachers_schedule:
                    if day in self.logic.teachers_schedule[t_name]:
                        if p in self.logic.teachers_schedule[t_name][day]:
                            class_set = self.logic.teachers_schedule[t_name][day][p]
                            if class_set:
                                info = list(class_set)[0]
                                g, c = str(info[0]), str(info[1])
                                self.add_cell(g, c, day, p, p, i+1)
                                found = True
                if not found and p <= config.PERIODS_PER_DAY[day]:
                    empty = QLabel()
                    empty.setStyleSheet(f"background-color: {COLORS['cell_default']}; border: 1px solid #e5e7eb;")
                    self.grid_layout.addWidget(empty, p, i+1)

    def render_subject(self):
        if not hasattr(self, 'combo_sel'): return
        subj_name = self.combo_sel.currentText()
        if not subj_name: return

        self.add_header("교시", 0, 0)
        for i, day in enumerate(config.DAYS):
            self.add_header(day, 0, i+1)
            self.grid_layout.setColumnStretch(i+1, 1)
            self.grid_layout.setColumnMinimumWidth(i+1, 120)

        for p in range(1, config.MAX_PERIODS + 1):
            self.add_header(f"{p}교시", p, 0)
            for i, day in enumerate(config.DAYS):
                if p <= config.PERIODS_PER_DAY[day]:
                    matches = []
                    classes = self.logic.get_all_sorted_classes()
                    for g, c in classes:
                        day_sched = self.logic.schedule[str(g)][str(c)].get(day, {})
                        info = day_sched.get(p)
                        if info:
                             # [수정] 유사 교과명을 체크하는 로직 적용
                            target_subject = info.get('subject')
                            if self.is_subject_similar(target_subject, subj_name):
                                matches.append(f"{g}-{c}({info['teacher']})")
                    
                    if matches:
                        lbl = QLabel("\n".join(matches))
                        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        lbl.setWordWrap(True)
                        lbl.setStyleSheet(f"background-color: {COLORS['cell_default']}; border: 1px solid #e5e7eb; font-size: 11px; padding: 2px;")
                        self.grid_layout.addWidget(lbl, p, i+1)
                    else:
                        empty = QLabel()
                        empty.setStyleSheet(f"background-color: {COLORS['cell_default']}; border: 1px solid #e5e7eb;")
                        self.grid_layout.addWidget(empty, p, i+1)
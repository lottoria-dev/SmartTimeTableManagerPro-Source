from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, QTextBrowser, QPushButton, QFrame, 
    QLabel, QSizePolicy, QTreeWidget, QTreeWidgetItem, QComboBox, QApplication, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QDrag, QColor

def apply_dialog_shadow(widget):
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(20)
    shadow.setColor(QColor(0, 0, 0, 30))
    shadow.setOffset(0, 5)
    widget.setGraphicsEffect(shadow)

class HelpDialog(QDialog):
    """도움말 팝업창"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("사용법 안내 - v3.0.0")
        self.resize(650, 600)
        self.setStyleSheet("background-color: #F8FAFC; color: #1e293b;") # 고급스러운 배경색
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        text_edit = QTextBrowser()
        text_edit.setOpenExternalLinks(True)
        text_edit.setFrameShape(QFrame.Shape.NoFrame)
        apply_dialog_shadow(text_edit)
        
        text_edit.setStyleSheet("""
            QTextBrowser {
                font-family: 'Pretendard', 'Malgun Gothic'; 
                font-size: 11pt; 
                color: #334155; 
                background-color: #ffffff;
                border-radius: 12px;
                padding: 15px;
            }
        """)
        
        help_content = """
<h2 style="color: #0f172a;">📖 스마트 시간표 매니저(Smart Timetable Manager Pro) v3.1.1</h2>
<hr style="border-top: 1px solid #e2e8f0; margin: 10px 0;">
<h3 style="color: #1d4ed8;">1. 기본 사용법</h3>
<ul style="line-height: 1.6;">
    <li><b>📂 불러오기:</b> CSV 형식의 시간표 파일을 불러옵니다.<br>
    <span style="font-size: 10pt; color: #64748b;">
    ※ 분리형, 병합형, 저장본 모두 지원<br>
    ※ <a href="https://mathtime.kr/?page=timetable" style="color: #0ea5e9; text-decoration: none;"><b>https://mathtime.kr/?page=timetable</b></a>의 예시 양식 활용 권장<br>
    ※ 엑셀에서 [내보내기] > [CSV(쉼표로 분리)]로 저장하여 사용
    </span></li>
    <li><b>🔍 보기 방식:</b> 요일별, 교사별 등 다양한 형태로 확인 가능하며, <b>📋 복사</b> 버튼으로 엑셀/한글에 바로 붙여넣을 수 있습니다.</li>
    <li><b>💾 저장:</b> 작업 내용을 언제든 CSV 파일로 백업할 수 있습니다.</li>
    <li><b>📜 내역:</b> 변경된 내역을 별도 창에서 확인합니다.</li>
</ul>

<h3 style="color: #1d4ed8;">2. 제어 패널(학년 제외 및 요일 변경)</h3>
<ul style="line-height: 1.6;">
    <li>각 요일 상단의 제어 패널을 통해 <b style="color: #b91c1c;">학년 단위로 행사/체험학습 등을 일괄 제외</b>할 수 있습니다.</li>
    <li>제외된 학년은 교환, 연쇄 이동 등의 대상에서 완벽히 배제됩니다.</li>
    <li><b>🔄 변경</b> 버튼을 통해 해당 요일의 모든 일과를 다른 요일의 기초 시간표로 손쉽게 덮어씌울 수 있습니다.</li>
</ul>

<h3 style="color: #1d4ed8;">3. 작업 모드 상세</h3>
<ul style="line-height: 1.6;">
    <li><b>조회 모드:</b> 수업 클릭 시 교사 일정 강조. 우클릭으로 개별 <b>🔒 잠금/해제</b> 가능.</li>
    <li><b>맞교환 모드:</b> 바꿀 두 수업을 차례로 클릭하거나 <b>드래그 앤 드롭</b>합니다.</li>
    <li><b>보강 모드:</b> 결강 수업 선택 후 대체 교사 배정.</li>
    <li><b>연쇄 이동 모드 (CHAIN):</b> 수동으로 연쇄적으로 밀어내며 이동시킵니다.</li>
    <li><b>✨ AI 자동 모드:</b> <b>[출발할 수업]</b>과 <b>[도착할 시간]</b>을 지정하면 AI가 최적의 이동 경로를 찾아 자동 재배치합니다.</li>
</ul>

<hr style="border-top: 1px solid #e2e8f0; margin: 15px 0;">
<div style="font-size: 10pt; color: #64748b; line-height: 1.6;">
    <b>■ 단축키 안내</b><br>
    - [Ctrl + O] 불러오기 / [Ctrl + S] 저장<br>
    - [Ctrl + Z] 실행취소 / [Ctrl + C] 클립보드 복사<br>
    - [1 ~ 5] 모드 빠른 전환<br>
    <br>
    <b>■ 개발자 정보</b><br>
    - 버전: 3.1.1<br>
    - 최종 업데이트: 2026.04.12.<br>
    - 문의: mathtime.ai@gmail.com<br>
    - 정식 배포 페이지를 제외한 곳에서 임의의 수정 및 재배포를 금지합니다.<br>
    © Copyright 2026 lottoria-dev. All rights reserved.
</div>
"""
        text_edit.setHtml(help_content)
        layout.addWidget(text_edit)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_close = QPushButton("닫기")
        btn_close.setMinimumWidth(100)
        btn_close.clicked.connect(self.accept)
        btn_close.setStyleSheet("""
            QPushButton { background-color: #3b82f6; color: white; border: none; border-radius: 8px; padding: 10px 20px; font-weight: bold; font-size: 12px;}
            QPushButton:hover { background-color: #2563eb; }
        """)
        apply_dialog_shadow(btn_close)
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)

class LogDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("변경 내역 (Log)")
        self.resize(550, 600)
        self.setStyleSheet("background-color: #F8FAFC; color: #1e293b;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["구분", "학반", "내용"])
        self.tree_widget.header().resizeSection(0, 70)
        self.tree_widget.header().resizeSection(1, 80)
        self.tree_widget.setIndentation(0)
        self.tree_widget.setAlternatingRowColors(True)
        
        self.tree_widget.setStyleSheet("""
            QTreeWidget {
                background-color: #ffffff; color: #334155; border-radius: 12px; border: none; outline: none;
            }
            QTreeWidget::item { height: 32px; border-bottom: 1px solid #f1f5f9; }
            QTreeWidget::item:alternate { background-color: #f8fafc; }
            QTreeWidget::item:selected { background-color: #e0f2fe; color: #0284c7; }
            QHeaderView::section {
                background-color: #f1f5f9; border: none; border-bottom: 2px solid #e2e8f0;
                padding: 8px; font-weight: 800; color: #475569;
            }
        """)
        apply_dialog_shadow(self.tree_widget)
        layout.addWidget(self.tree_widget)
        
        layout.addSpacing(10)
        
        btn_layout = QHBoxLayout()
        
        self.btn_copy_stats = QPushButton("📊 결보강 통계 엑셀 복사")
        self.btn_copy_stats.clicked.connect(self.copy_stats)
        self.btn_copy_stats.setStyleSheet("""
            QPushButton { background-color: #10b981; color: white; border: none; border-radius: 8px; padding: 10px; font-weight: bold; }
            QPushButton:hover { background-color: #059669; }
        """)
        apply_dialog_shadow(self.btn_copy_stats)
        btn_layout.addWidget(self.btn_copy_stats)
        
        btn_layout.addStretch()

        btn_close = QPushButton("닫기")
        btn_close.setMinimumWidth(80)
        btn_close.clicked.connect(self.accept)
        btn_close.setStyleSheet("""
            QPushButton { background-color: #64748b; color: white; border: none; border-radius: 8px; padding: 10px; font-weight: bold;}
            QPushButton:hover { background-color: #475569; }
        """)
        apply_dialog_shadow(btn_close)
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
    clicked = Signal(object)
    right_clicked = Signal(object)
    cell_dropped = Signal(object, object) 

    def __init__(self, data_key, parent=None):
        super().__init__(parent)
        self.data_key = data_key
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setObjectName("Cell")
        
        self.setAcceptDrops(True) 
        self.drag_start_position = None
        
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        self.setMinimumHeight(32)

        # [최적화] 수백 개의 셀에 개별적으로 그림자를 적용하면 렌더링 부하(스크롤 렉)가 심해집니다.
        # 따라서 셀의 QGraphicsDropShadowEffect 연산을 제거하여 스크롤 성능을 비약적으로 높였습니다.

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        self.layout.addStretch(1)
        
        self.lbl_main = QLabel()
        self.lbl_main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_main.setWordWrap(True)
        self.lbl_main.setStyleSheet("font-weight: 800; font-size: 11px; border: none; background-color: transparent; padding: 0px; margin: 0px; margin-bottom: -1px;")
        
        self.lbl_sub = QLabel()
        self.lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_sub.setStyleSheet("color: #64748b; font-size: 10px; border: none; background-color: transparent; padding: 0px; margin: 0px; margin-top: -1px;")
        
        self.layout.addWidget(self.lbl_main)
        self.layout.addWidget(self.lbl_sub)
        
        self.layout.addStretch(1)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.pos() 
            self.clicked.emit(self.data_key) 
        elif event.button() == Qt.MouseButton.RightButton:
            self.right_clicked.emit(self.data_key)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton): return
        if not self.drag_start_position: return
        
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
            
        drag = QDrag(self)
        mime_data = QMimeData()
        
        key_str = "|".join(map(str, self.data_key))
        mime_data.setText(key_str)
        drag.setMimeData(mime_data)
        
        drag.exec(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        src_key_str = event.mimeData().text()
        src_parts = src_key_str.split('|')
        
        if src_parts[0] == "TEACHER_VIEW":
            src_key = ("TEACHER_VIEW", src_parts[1], src_parts[2], int(src_parts[3]))
        else:
            src_key = (src_parts[0], src_parts[1], src_parts[2], int(src_parts[3]))
            
        self.cell_dropped.emit(src_key, self.data_key)
        event.acceptProposedAction()

    def set_content(self, main_text, sub_text, bg_color, border_color=None, border_width=1, text_color=None):
        self.lbl_main.setText(main_text)
        self.lbl_sub.setText(sub_text)
        
        if not text_color: text_color = "#1e293b"
        
        main_style = f"font-size: 11px; border: none; background-color: transparent; padding: 0px; margin: 0px; margin-bottom: -1px; font-weight: 800; color: {text_color};"
        self.lbl_main.setStyleSheet(main_style)

        # [최적화] 복잡한 rgba 그라데이션 및 다중 테두리를 단순하고 세련된 단일 테두리로 변경하여 렌더링 성능 확보
        if not border_color or border_color == "rgba(226, 232, 240, 0.8)":
            border_css = "border: 1px solid #cbd5e1;" # 깔끔하고 가벼운 단색 테두리
        else:
            border_css = f"border: {border_width}px solid {border_color};"

        base_style = f"""
            background-color: {bg_color}; 
            border-radius: 6px;
            {border_css}
            padding: 0px;
        """
        
        hover_style = f"""
            QFrame#Cell:hover {{
                border: 2px solid #94a3b8;
                background-color: {bg_color}; 
            }}
        """

        self.setStyleSheet(f"QFrame#Cell {{ {base_style} }} {hover_style}")
        
class DayRoutineDialog(QDialog):
    def __init__(self, target_day, parent=None):
        super().__init__(parent)
        self.target_day = target_day
        self.setWindowTitle(f"{target_day} 일과 변경")
        self.resize(360, 180)
        self.setStyleSheet("background-color: #F8FAFC; color: #1e293b;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        lbl_info = QLabel("선택한 요일의 전체 일과를 덮어씁니다.\n(학사일정 변경 전용 - 개별 결보강 통계에서 제외됨)")
        lbl_info.setStyleSheet("color: #475569; font-size: 10pt; margin-bottom: 10px; font-weight: bold;")
        layout.addWidget(lbl_info)
        
        form_layout = QHBoxLayout()
        
        self.combo_src = QComboBox()
        import config
        self.combo_src.addItems(config.DAYS) 
        self.combo_src.setStyleSheet("padding: 5px; border-radius: 4px; border: 1px solid #cbd5e1; background: white;")
        
        lbl_arrow = QLabel(" ➔ ")
        lbl_arrow.setStyleSheet("font-weight: 800; color: #3b82f6; font-size: 16px;")
        
        lbl_tgt = QLabel(f"{target_day}")
        lbl_tgt.setStyleSheet("font-weight: 800; color: #ef4444; padding: 4px; font-size: 14px;")
        
        lbl1 = QLabel("가져올 일과:")
        lbl1.setStyleSheet("font-weight: bold; color: #334155;")
        lbl2 = QLabel("덮어쓸 요일:")
        lbl2.setStyleSheet("font-weight: bold; color: #334155;")
        
        form_layout.addWidget(lbl1)
        form_layout.addWidget(self.combo_src)
        form_layout.addWidget(lbl_arrow)
        form_layout.addWidget(lbl2)
        form_layout.addWidget(lbl_tgt)
        
        layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_cancel = QPushButton("취소")
        btn_cancel.setStyleSheet("""
            QPushButton { background-color: #e2e8f0; color: #475569; padding: 8px 15px; border-radius: 6px; border: none; font-weight: bold;}
            QPushButton:hover { background-color: #cbd5e1; }
        """)
        btn_cancel.clicked.connect(self.reject)
        
        btn_apply = QPushButton("적용하기")
        btn_apply.setStyleSheet("""
            QPushButton { background-color: #ef4444; color: white; font-weight: bold; padding: 8px 15px; border-radius: 6px; border: none; }
            QPushButton:hover { background-color: #dc2626; }
        """)
        btn_apply.clicked.connect(self.accept)
        
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_apply)
        
        layout.addStretch()
        layout.addLayout(btn_layout)
        
    def get_source_day(self):
        return self.combo_src.currentText()

class ChangeDetailDialog(QDialog):
    """조회 모드 변동 내역 상세 팝업창"""
    def __init__(self, title, details, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(400, 280)
        
        # 다크모드 무시 (명시적 라이트 테마) 및 윈도우 투명도(알파값) 설정
        self.setStyleSheet("background-color: #F8FAFC; color: #1e293b;")
        self.setWindowOpacity(0.95)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        text_edit = QTextBrowser()
        text_edit.setPlainText(details)
        text_edit.setFrameShape(QFrame.Shape.NoFrame)
        apply_dialog_shadow(text_edit)
        
        text_edit.setStyleSheet("""
            QTextBrowser {
                font-family: 'Pretendard', 'Malgun Gothic'; 
                font-size: 10pt; 
                color: #334155; 
                background-color: #ffffff;
                border-radius: 8px;
                padding: 12px;
                border: 1px solid #e2e8f0;
            }
        """)
        layout.addWidget(text_edit)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_close = QPushButton("확인")
        btn_close.setMinimumWidth(80)
        btn_close.clicked.connect(self.accept)
        btn_close.setStyleSheet("""
            QPushButton { background-color: #0ea5e9; color: white; border: none; border-radius: 6px; padding: 8px 16px; font-weight: bold;}
            QPushButton:hover { background-color: #0284c7; }
        """)
        apply_dialog_shadow(btn_close)
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)
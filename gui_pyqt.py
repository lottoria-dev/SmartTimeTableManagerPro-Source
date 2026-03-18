import sys
import os
import re  
from datetime import datetime 
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFrame, QScrollArea, QGridLayout, 
    QComboBox, QMessageBox, QFileDialog, QSplitter, QButtonGroup, 
    QRadioButton, QCheckBox, QAbstractItemView, QSizePolicy, 
    QDialog, QTextEdit, QLayout
)
from PySide6.QtCore import Qt, Signal, QSize, QMimeData 
from PySide6.QtGui import QFont, QColor, QPalette, QIcon, QKeyEvent, QCloseEvent

import config
from logic import TimetableLogic
from ai_mover import AIChainedMover

from gui_styles import STYLE_SHEET, COLORS
from gui_components import HelpDialog, ClickableFrame, LogDialog

# [리팩토링] 분리된 매니저 클래스들 임포트
from gui_clipboard import ClipboardManager
from gui_interaction import CellInteractionHandler
from gui_grid_renderer import GridRenderer

class TimetableWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Timetable Manager Pro v2.3.1")
        self.resize(1520, 750)
        
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
        self.cell_widget_map = {}
        
        self.log_dialog = LogDialog(self)
        
        # [리팩토링] 기능별 전담 매니저 생성
        self.clipboard_manager = ClipboardManager(self)
        self.interaction_handler = CellInteractionHandler(self)
        self.grid_renderer = GridRenderer(self)

        self.init_ui()

    def force_light_palette(self):
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(31, 41, 55))
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
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(5)

        # 1. 상단 컨트롤 패널
        top_panel = QFrame()
        top_panel.setObjectName("Card")
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(10, 8, 10, 8)
        top_layout.setSpacing(10)

        # [좌측] 버튼 그룹
        btn_group_layout = QHBoxLayout()
        btn_group_layout.setSpacing(5)
        
        self.btn_load = QPushButton("📂 불러오기")
        self.btn_load.clicked.connect(self.load_csv)
        self.btn_save = QPushButton("💾 저장")
        self.btn_save.clicked.connect(self.save_csv)
        self.btn_save.setObjectName("SuccessBtn")
        
        self.btn_copy = QPushButton("📋 복사")
        self.btn_copy.clicked.connect(self.copy_to_clipboard) # 위임 처리
        self.btn_copy.setObjectName("InfoBtn")
        
        self.btn_undo = QPushButton("↩ 실행취소")
        self.btn_undo.clicked.connect(self.undo_action)
        self.btn_cancel = QPushButton("🚫 선택해제")
        self.btn_cancel.clicked.connect(self.cancel_action)
        self.btn_cancel.setObjectName("DangerBtn")
        
        btn_group_layout.addWidget(self.btn_load)
        btn_group_layout.addWidget(self.btn_save)
        btn_group_layout.addWidget(self.btn_copy) 
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
            ("🔗 연쇄모드", "CHAIN", False),
            ("🤖 AI자동", "CHAIN", True)
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
        btn_apply_cover.clicked.connect(self.execute_cover) # 위임 처리
        btn_apply_cover.setObjectName("PrimaryBtn")
        cover_layout.addWidget(self.combo_cover_teacher)
        cover_layout.addWidget(btn_apply_cover)
        self.cover_widget.setVisible(False)
        self.context_layout.addWidget(self.cover_widget)

        top_layout.addLayout(btn_group_layout)
        top_layout.addWidget(line1)
        top_layout.addLayout(mode_group_layout)
        top_layout.addWidget(line2)
        top_layout.addWidget(self.context_stack)
        top_layout.addStretch()
        
        btn_log = QPushButton("📜 내역")
        btn_log.clicked.connect(self.show_log_dialog)
        top_layout.addWidget(btn_log)

        btn_reset = QPushButton("초기화")
        btn_reset.clicked.connect(self.reset_all)
        top_layout.addWidget(btn_reset)
        
        btn_help = QPushButton("❓ 도움말")
        btn_help.clicked.connect(self.show_help)
        top_layout.addWidget(btn_help)

        main_layout.addWidget(top_panel)

        # 2. 메인 콘텐츠
        grid_group = QFrame()
        grid_group.setObjectName("Card")
        grid_group_layout = QVBoxLayout(grid_group)
        grid_group_layout.setContentsMargins(0, 0, 0, 0)

        option_bar = QFrame()
        option_bar.setStyleSheet("background-color: #f9fafb; border-bottom: 1px solid #e5e7eb;")
        option_layout = QHBoxLayout(option_bar)
        option_layout.setContentsMargins(10, 5, 10, 5) 
        option_layout.addWidget(QLabel("보기 방식:"))
        
        self.view_btn_group = QButtonGroup(self)
        self.view_btn_group.buttonClicked.connect(self.on_view_change)
        view_modes = [
            ("주간 전체", "ALL_WEEK"), 
            ("교사 전체", "ALL_TEACHER"),
            ("요일별", "ALL_DAY"), 
            ("학급별", "SINGLE"), 
            ("교사별", "TEACHER"), 
            ("교과별", "SUBJECT")
        ]
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
        
        self.chk_only_changed = QCheckBox("🔄 변경된 항목만 보기")
        self.chk_only_changed.stateChanged.connect(self.refresh_grid)
        self.chk_only_changed.setStyleSheet("""
            QCheckBox {
                font-weight: bold; color: #d97706; margin-left: 15px;
                border: 1px solid #9ca3af; border-radius: 5px;
                padding: 4px 8px; background-color: #ffffff;
            }
            QCheckBox:hover { background-color: #f3f4f6; }
        """)
        option_layout.addWidget(self.chk_only_changed)
        option_layout.addStretch()

        grid_group_layout.addWidget(option_bar)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.scroll_area.setWidget(self.grid_container)
        
        grid_group_layout.addWidget(self.scroll_area)
        
        self.status_bar = QLabel(" 파일을 불러와주세요.")
        self.status_bar.setFixedHeight(24) 
        self.status_bar.setStyleSheet("background-color: #ffffff; color: #3b82f6; font-weight: bold; padding-left: 10px; font-size: 11px;")
        grid_group_layout.addWidget(self.status_bar)

        main_layout.addWidget(grid_group)

    def closeEvent(self, event: QCloseEvent):
        if self.logic.is_modified:
            reply = QMessageBox.question(
                self, "종료 확인", "변경된 내용이 저장되지 않았습니다.\n저장하고 종료하시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.save_csv()
                if self.logic.is_modified: 
                    event.ignore()
                    return
                event.accept()
            elif reply == QMessageBox.StandardButton.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def show_log_dialog(self):
        self.log_dialog.show()
        self.log_dialog.raise_()
        self.log_dialog.activateWindow()

    def show_help(self):
        HelpDialog(self).exec()

    # --- 기능 및 상태 관리 래퍼 (Wrapper) ---
    def load_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "CSV 파일 열기", "", "CSV Files (*.csv)")
        if not file_path: return
        success, msg = self.logic.import_school_csv(file_path)
        if success:
            self.status_bar.setText(f"✅ {msg}")
            self.status_bar.setStyleSheet("color: #10b981; font-weight: bold; padding-left: 10px; font-size: 11px;")
            self.view_mode = "ALL_WEEK"
            self.refresh_selectors()
            self.refresh_grid()
            self.update_log_view()
        else:
            QMessageBox.critical(self, "오류", msg)

    def save_csv(self):
        if not self.logic.schedule: return
        current_time = datetime.now().strftime("%y%m%d%H%M%S")
        file_path, _ = QFileDialog.getSaveFileName(self, "CSV 파일 저장", f"timetable-{current_time}.csv", "CSV Files (*.csv)")
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
        self.status_bar.setStyleSheet(f"color: {COLORS['accent']}; font-weight: bold; padding-left: 10px; font-size: 11px;")
        self.update_cell_visuals()

    def on_view_change(self, btn):
        self.view_mode = btn.property("view_val")
        self.refresh_selectors()
        self.refresh_grid()

    def update_log_view(self):
        logs = self.logic.get_diff_list() if hasattr(self.logic, 'get_diff_list') else self.logic.change_logs
        self.log_dialog.update_logs(logs)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.cancel_action()
        else:
            super().keyPressEvent(event)

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
            self.adjust_combo_width(self.combo_sel)
            self.combo_sel.currentTextChanged.connect(self.refresh_grid)
            self.selector_layout.addWidget(self.combo_sel)
        elif self.view_mode == "TEACHER":
            self.selector_layout.addWidget(QLabel("교사:"))
            self.combo_sel = QComboBox()
            teachers = self.logic.get_all_teachers_sorted()
            self.combo_sel.addItems(teachers)
            self.adjust_combo_width(self.combo_sel)
            self.combo_sel.currentTextChanged.connect(self.refresh_grid)
            self.selector_layout.addWidget(self.combo_sel)
        elif self.view_mode == "SUBJECT":
            self.selector_layout.addWidget(QLabel("교과:"))
            self.combo_sel = QComboBox()
            
            all_subjects = set()
            if self.logic.schedule:
                for g_data in self.logic.schedule.values():
                    for c_data in g_data.values():
                        for day_data in c_data.values():
                            for info in day_data.values():
                                if info and 'subject' in info:
                                    all_subjects.add(info['subject'])
            
            def subject_sort_key(s):
                has_alnum = any(c.isascii() and c.isalnum() for c in s)
                return (has_alnum, len(s), s)

            sorted_subjects = sorted(list(all_subjects), key=subject_sort_key)
            representatives = []

            for subj in sorted_subjects:
                is_covered = False
                for rep in representatives:
                    if self.is_subject_similar(rep, subj):
                        is_covered = True
                        break
                if not is_covered:
                    representatives.append(subj)
            
            representatives.sort()
            self.combo_sel.addItems(representatives)
            self.adjust_combo_width(self.combo_sel)
            self.combo_sel.currentTextChanged.connect(self.refresh_grid)
            self.selector_layout.addWidget(self.combo_sel)

    def adjust_combo_width(self, combo):
        width = 0
        fm = combo.fontMetrics()
        for i in range(combo.count()):
            w = fm.horizontalAdvance(combo.itemText(i))
            if w > width: width = w
        combo.setMinimumWidth(width + 40)

    # 공통 유틸리티 (다른 매니저 클래스들에서 공유)
    def is_subject_similar(self, target, selected):
        if not target or not selected: return False
        t = target.replace(" ", "")
        s = selected.replace(" ", "")
        
        if t == s: return True
        if s in t or t in s: return True
        
        if t[0] == s[0]:
            has_extra_t = any(c.isascii() and c.isalnum() for c in t)
            has_extra_s = any(c.isascii() and c.isalnum() for c in s)
            if has_extra_t or has_extra_s:
                return True
        return False

    # --- 분리된 매니저로의 위임(Delegation) ---
    def copy_to_clipboard(self):
        self.clipboard_manager.copy_to_clipboard()

    def refresh_grid(self, _=None):
        self.grid_renderer.refresh_grid(_)

    def update_cell_visuals(self):
        self.grid_renderer.update_cell_visuals()

    def execute_cover(self):
        self.interaction_handler.execute_cover()